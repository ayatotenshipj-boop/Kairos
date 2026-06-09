import logging
import time
from html import escape
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import QFileDialog

from kairos.config import config as cfg
from kairos.config.defaults import DEFAULT_CONFIG
from kairos.pipeline.logger import log_session
from kairos.ui.workers import (
    AuthCheckWorker,
    ExtractionWorker,
    ProcessorWorker,
    WriterWorker,
    _fmt_duration,
)

logger = logging.getLogger(__name__)


class Backend(QObject):
    statusChanged        = Signal()
    canProcessChanged    = Signal()
    promptLabelsChanged  = Signal()
    pipelinePhaseChanged = Signal()
    reduceMotionChanged  = Signal()
    elapsedChanged       = Signal()
    settingsError        = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_text: str = ""
        self._status_state: str = "idle"
        self._can_process: bool = False
        self._prompt_labels: list = []
        self._prompts: list[dict] = []
        self._pipeline_phase: str = ""
        self._reduce_motion: bool = bool(cfg.load().get("reduce_motion", False))
        self._elapsed_text: str = ""
        self._loaded_source: str | None = None
        self._pipeline_source: str | None = None
        self._current_prompt_label: str | None = None
        self._current_mode: str = "notebooklm"
        self._session_start: float | None = None
        self._extraction_worker: ExtractionWorker | None = None
        self._processor_worker: ProcessorWorker | None = None
        self._writer_worker: WriterWorker | None = None
        self._auth_worker: AuthCheckWorker | None = None
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._tick_elapsed)
        self._load_prompts()
        # Verificação de sessão no startup, deferida para o event loop (não bloqueia).
        QTimer.singleShot(0, self._run_startup_auth_check)

    # ── Properties ────────────────────────────────────────────────────────

    @Property(str, notify=statusChanged)
    def statusText(self) -> str:
        return self._status_text

    @Property(str, notify=statusChanged)
    def statusState(self) -> str:
        return self._status_state

    @Property(bool, notify=canProcessChanged)
    def canProcess(self) -> bool:
        return self._can_process

    @Property('QVariantList', notify=promptLabelsChanged)
    def promptLabels(self) -> list:
        return self._prompt_labels

    @Property(str, notify=pipelinePhaseChanged)
    def pipelinePhase(self) -> str:
        return self._pipeline_phase

    @Property(bool, notify=reduceMotionChanged)
    def reduceMotion(self) -> bool:
        return self._reduce_motion

    @Property(str, notify=elapsedChanged)
    def elapsedText(self) -> str:
        return self._elapsed_text

    # ── Internal helpers ───────────────────────────────────────────────────

    def _set_status(self, text: str, state: str = "idle") -> None:
        self._status_text = text
        self._status_state = state
        self.statusChanged.emit()

    def _set_can_process(self, value: bool) -> None:
        if self._can_process != value:
            self._can_process = value
            self.canProcessChanged.emit()

    def _set_phase(self, phase: str) -> None:
        if self._pipeline_phase != phase:
            self._pipeline_phase = phase
            self.pipelinePhaseChanged.emit()

    def _session_elapsed(self) -> float:
        if self._session_start is None:
            return 0.0
        return time.monotonic() - self._session_start

    def _tick_elapsed(self) -> None:
        self._elapsed_text = _fmt_duration(self._session_elapsed())
        self.elapsedChanged.emit()

    def _stop_elapsed(self) -> None:
        self._elapsed_timer.stop()

    def _load_prompts(self) -> None:
        config = cfg.load()
        prompts_raw = config.get("prompts", DEFAULT_CONFIG["prompts"])
        valid: list[dict] = []
        for p in prompts_raw:
            if not isinstance(p, dict):
                continue
            if "label" not in p or "text" not in p:
                continue
            if not p["label"].strip() or not p["text"].strip():
                continue
            valid.append(p)
        if not valid:
            valid = list(DEFAULT_CONFIG["prompts"])
        self._prompts = valid
        self._prompt_labels = [p["label"] for p in self._prompts]
        self.promptLabelsChanged.emit()

    def _run_startup_auth_check(self) -> None:
        """Verifica a sessão do NotebookLM no startup, se for o backend ativo."""
        backend = cfg.load().get("processor_backend", "notebooklm")
        if backend != "notebooklm":
            return
        self._auth_worker = AuthCheckWorker()
        self._auth_worker.finished.connect(self._on_auth_check_finished)
        self._auth_worker.start()

    def _on_auth_check_finished(self, ok: bool, msg: str) -> None:
        worker = self.sender()
        if worker is not self._auth_worker:
            return
        self._auth_worker.finished.disconnect(self._on_auth_check_finished)
        self._auth_worker = None
        # Só avisa se a sessão caiu e nada foi carregado ainda (não atropela
        # status de "Pronto"/pipeline em curso). O fallback real ocorre no
        # processor durante o processamento.
        if not ok and self._loaded_source is None:
            self._set_status(msg, "warning")

    # ── Public slots ───────────────────────────────────────────────────────

    @Slot(str)
    def loadSource(self, source: str) -> None:
        source = source.strip()
        if not source:
            return
        # Normaliza URI file:// para caminho local
        if source.startswith("file://"):
            from PySide6.QtCore import QUrl
            source = QUrl(source).toLocalFile()
        is_youtube = "youtube.com" in source or "youtu.be" in source
        if is_youtube:
            self._loaded_source = source
            display = source if len(source) <= 52 else source[:49] + "..."
            self._set_status(f"Pronto: {display}", "idle")
            self._set_can_process(True)
        elif Path(source).suffix.lower() == ".pdf":
            path = Path(source)
            if not path.is_file():
                self._set_status("Arquivo não encontrado", "error")
                return
            self._loaded_source = source
            self._set_status(f"Pronto: {path.name}", "idle")
            self._set_can_process(True)
        else:
            self._set_status("Fonte inválida — use um PDF ou URL do YouTube", "error")

    @Slot(int)
    def process(self, prompt_index: int) -> None:
        if not self._loaded_source:
            self._set_status("Erro: nenhum arquivo carregado", "error")
            return
        if any(
            w is not None and w.isRunning()
            for w in (self._extraction_worker, self._processor_worker, self._writer_worker)
        ):
            return

        self._pipeline_source = self._loaded_source
        if prompt_index < 0 or prompt_index >= len(self._prompts):
            self._set_status("Erro: prompt não encontrado", "error")
            return
        self._current_prompt_label = self._prompts[prompt_index]["label"]

        self._set_can_process(False)
        is_youtube = self._pipeline_source.startswith("http")
        self._set_status(
            "Buscando transcrição..." if is_youtube else "Extraindo texto...",
            "running",
        )
        self._set_phase("extracting")
        self._session_start = time.monotonic()
        self._elapsed_text = _fmt_duration(0)
        self.elapsedChanged.emit()
        self._elapsed_timer.start()

        self._extraction_worker = ExtractionWorker(self._pipeline_source)
        self._extraction_worker.finished.connect(self._on_extraction_finished)
        self._extraction_worker.error.connect(self._on_extraction_error)
        self._extraction_worker.start()

    @Slot()
    def reloadPrompts(self) -> None:
        self._load_prompts()

    @Slot()
    def onAppClose(self) -> None:
        self._elapsed_timer.stop()
        for worker in (
            self._extraction_worker,
            self._processor_worker,
            self._writer_worker,
            self._auth_worker,
        ):
            if worker is not None and worker.isRunning():
                try:
                    worker.finished.disconnect()
                    if hasattr(worker, "error"):
                        worker.error.disconnect()
                except (TypeError, RuntimeError):
                    pass
                worker.quit()
                worker.wait(3000)
                if worker.isRunning():
                    worker.terminate()
                    worker.wait(1000)
        from kairos.integrations import launcher
        launcher.stop()

    @Slot(result='QVariantMap')
    def getSettings(self) -> dict:
        config = cfg.load()
        return {
            "obsidian_vault_path": config.get("obsidian_vault_path", ""),
            "simpmusic_path": config.get("simpmusic_path", ""),
            "reduce_motion": bool(config.get("reduce_motion", False)),
            "processor_backend": config.get("processor_backend", "notebooklm"),
            "gemini_api_key": config.get("gemini_api_key", ""),
            "gemini_model": config.get("gemini_model", DEFAULT_CONFIG["gemini_model"]),
            "ollama_model": config.get("ollama_model", DEFAULT_CONFIG["ollama_model"]),
            "prompts": config.get("prompts", list(DEFAULT_CONFIG["prompts"])),
        }

    @Slot('QVariantMap')
    def saveSettings(self, settings: dict) -> None:
        try:
            config = cfg.load()
            config["obsidian_vault_path"] = str(settings.get("obsidian_vault_path", "") or "")
            config["simpmusic_path"] = str(settings.get("simpmusic_path", "") or "")
            new_reduce_motion = bool(settings.get("reduce_motion", False))
            config["reduce_motion"] = new_reduce_motion
            backend = str(settings.get("processor_backend", "") or "notebooklm")
            config["processor_backend"] = (
                backend if backend in ("notebooklm", "gemini", "ollama") else "notebooklm"
            )
            config["gemini_api_key"] = str(settings.get("gemini_api_key", "") or "")
            config["gemini_model"] = (
                str(settings.get("gemini_model", "") or "").strip()
                or DEFAULT_CONFIG["gemini_model"]
            )
            config["ollama_model"] = (
                str(settings.get("ollama_model", "") or "").strip()
                or DEFAULT_CONFIG["ollama_model"]
            )
            prompts_raw = settings.get("prompts", [])
            valid: list[dict] = []
            for p in prompts_raw:
                label = str(p.get("label", "") or "").strip()
                text = str(p.get("text", "") or "").strip()
                if label and text:
                    valid.append({
                        "id": str(p.get("id", "") or ""),
                        "label": label,
                        "text": text,
                    })
            config["prompts"] = valid if valid else list(DEFAULT_CONFIG["prompts"])
            cfg.save(config)
            self._load_prompts()
            if self._reduce_motion != new_reduce_motion:
                self._reduce_motion = new_reduce_motion
                self.reduceMotionChanged.emit()
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            self.settingsError.emit(f"Erro ao salvar configurações: {e}")

    @Slot(str, bool, result=str)
    def browseForPath(self, current: str, is_directory: bool) -> str:
        start = current if current and Path(current).exists() else str(Path.home())
        if is_directory:
            path = QFileDialog.getExistingDirectory(None, "Selecionar pasta", start)
        else:
            path, _ = QFileDialog.getOpenFileName(None, "Selecionar arquivo", start)
        return path or ""

    # ── Controles de música (Simpmusic via MPRIS) ──────────────────────────

    @Slot()
    def musicPlayPause(self) -> None:
        from kairos.integrations import launcher
        launcher.play_pause()

    @Slot(int)
    def musicVolume(self, direction: int) -> None:
        from kairos.integrations import launcher
        launcher.volume_step(0.05 if direction >= 0 else -0.05)

    # ── Worker callbacks ───────────────────────────────────────────────────

    def _on_extraction_finished(self, text: str) -> None:
        worker = self.sender()
        if worker is not self._extraction_worker:
            return
        self._extraction_worker.finished.disconnect(self._on_extraction_finished)
        self._extraction_worker.error.disconnect(self._on_extraction_error)
        self._extraction_worker = None

        prompt_obj = next(
            (p for p in self._prompts if p["label"] == self._current_prompt_label),
            None,
        )
        if not prompt_obj:
            self._stop_elapsed()
            self._set_status("Erro: prompt não encontrado", "error")
            self._set_phase("error_extraction")
            self._set_can_process(True)
            return

        self._set_status("Conectando ao NotebookLM...", "running")
        self._set_phase("processing")
        self._processor_worker = ProcessorWorker(text, prompt_obj["text"])
        self._processor_worker.finished.connect(self._on_processing_finished)
        self._processor_worker.error.connect(self._on_processing_error)
        self._processor_worker.start()

    def _on_extraction_error(self, error_msg: str) -> None:
        worker = self.sender()
        if worker is not self._extraction_worker:
            return
        self._stop_elapsed()
        self._set_status(f"Erro: {error_msg}", "error")
        self._set_phase("error_extraction")
        self._set_can_process(True)
        self._extraction_worker.finished.disconnect(self._on_extraction_finished)
        self._extraction_worker.error.disconnect(self._on_extraction_error)
        self._extraction_worker = None
        log_session(
            source=self._pipeline_source or "",
            prompt_label=self._current_prompt_label or "",
            status="✗",
            duration_seconds=self._session_elapsed(),
            mode="local",
        )

    def _on_processing_finished(self, result: str, mode: str) -> None:
        worker = self.sender()
        if worker is not self._processor_worker:
            return
        self._processor_worker.finished.disconnect(self._on_processing_finished)
        self._processor_worker.error.disconnect(self._on_processing_error)
        self._processor_worker = None
        self._current_mode = mode
        self._set_status("Salvando nota no Obsidian...", "running")
        self._set_phase("writing")

        self._writer_worker = WriterWorker(
            result,
            self._pipeline_source,
            self._current_prompt_label or "",
            mode,
            session_duration=_fmt_duration(self._session_elapsed()),
        )
        self._writer_worker.finished.connect(self._on_write_finished)
        self._writer_worker.error.connect(self._on_write_error)
        self._writer_worker.start()

    def _on_processing_error(self, error_msg: str) -> None:
        worker = self.sender()
        if worker is not self._processor_worker:
            return
        self._stop_elapsed()
        self._set_status(f"Erro no processamento: {error_msg}", "error")
        self._set_phase("error_processing")
        self._set_can_process(True)
        self._processor_worker.finished.disconnect(self._on_processing_finished)
        self._processor_worker.error.disconnect(self._on_processing_error)
        self._processor_worker = None
        log_session(
            source=self._pipeline_source or "",
            prompt_label=self._current_prompt_label or "",
            status="✗",
            duration_seconds=self._session_elapsed(),
            mode="local",
        )

    def _on_write_finished(self, path: str) -> None:
        worker = self.sender()
        if worker is not self._writer_worker:
            return
        self._stop_elapsed()
        elapsed = self._session_elapsed()
        filename = escape(Path(path).name)
        uri = Path(path).as_uri()
        link = f'<a href="{uri}" style="color: #e8903c;">{filename}</a>'
        if self._current_mode == "fallback":
            self._set_status(
                f"⚠ Salvo localmente — backend de IA indisponível: {link}",
                "warning",
            )
        else:
            self._set_status(f"Nota salva: {link}", "success")
        self._set_phase("done")
        self._set_can_process(True)
        self._writer_worker.finished.disconnect(self._on_write_finished)
        self._writer_worker.error.disconnect(self._on_write_error)
        self._writer_worker = None
        log_session(
            source=self._pipeline_source or "",
            prompt_label=self._current_prompt_label or "",
            status="✓" if self._current_mode != "fallback" else "⚠ local",
            duration_seconds=elapsed,
            mode=self._current_mode,
        )

    def _on_write_error(self, error_msg: str) -> None:
        worker = self.sender()
        if worker is not self._writer_worker:
            return
        self._stop_elapsed()
        elapsed = self._session_elapsed()
        self._set_status(error_msg, "error")
        self._set_phase("error_writing")
        self._set_can_process(True)
        self._writer_worker.finished.disconnect(self._on_write_finished)
        self._writer_worker.error.disconnect(self._on_write_error)
        self._writer_worker = None
        log_session(
            source=self._pipeline_source or "",
            prompt_label=self._current_prompt_label or "",
            status="✗",
            duration_seconds=elapsed,
            mode="local",
        )
