import logging
import time
from html import escape
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, QUrlQuery, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog

from kairos.config import config as cfg
from kairos.config.defaults import DEFAULT_CONFIG, STRUCTURE_INSTRUCTION
from kairos.pipeline.audio_extractor import AUDIO_SUFFIXES
from kairos.pipeline.text_extractor import TEXT_SUFFIXES
from kairos.pipeline.logger import log_session
from kairos.util import format_duration as _fmt_duration
from kairos._version import __version__
from kairos.ui.workers import (
    AuthCheckWorker,
    ExtractionWorker,
    MusicWorker,
    ProcessorWorker,
    UpdateCheckWorker,
    WriterWorker,
)

logger = logging.getLogger(__name__)

# Rótulo legível de cada backend, para status e pipeline tracker.
_BACKEND_LABELS = {"notebooklm": "NotebookLM", "gemini": "Gemini", "ollama": "Local"}


class Backend(QObject):
    statusChanged        = Signal()
    canProcessChanged    = Signal()
    promptLabelsChanged  = Signal()
    pipelinePhaseChanged = Signal()
    reduceMotionChanged  = Signal()
    themeChanged         = Signal()
    progressChanged      = Signal()
    graphChanged         = Signal()
    musicChanged         = Signal()
    backendLabelChanged  = Signal()
    updateInfoChanged    = Signal()
    settingsError        = Signal(str)
    settingsSaved        = Signal()
    # Falha que exige escolha do usuário: (título, descrição) em PT-BR.
    decisionNeeded       = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_text: str = ""
        self._status_state: str = "idle"
        self._can_process: bool = False
        self._prompt_labels: list = []
        self._prompts: list[dict] = []
        self._pipeline_phase: str = ""
        _boot_cfg = cfg.load()
        self._reduce_motion: bool = bool(_boot_cfg.get("reduce_motion", False))
        self._dark_mode: bool = bool(_boot_cfg.get("dark_mode", True))
        self._progress: int = 0
        self._graph_data: dict = {}
        self._music: dict = {
            "status": "Stopped", "title": "", "artist": "",
            "artUrl": "", "canNext": False, "canPrev": False,
            "available": False,
        }
        self._loaded_source: str | None = None
        self._pipeline_source: str | None = None
        self._current_prompt_label: str | None = None
        self._current_mode: str = "notebooklm"
        self._pending_text: str | None = None  # texto extraído à espera de decisão
        self._backend_label: str = _BACKEND_LABELS.get(
            _boot_cfg.get("processor_backend", "notebooklm"), "NotebookLM"
        )
        self._session_start: float | None = None
        self._extraction_worker: ExtractionWorker | None = None
        self._processor_worker: ProcessorWorker | None = None
        self._writer_worker: WriterWorker | None = None
        self._auth_worker: AuthCheckWorker | None = None
        self._music_worker: MusicWorker | None = None
        self._update_info: dict = {"available": False, "version": "", "url": "", "current": __version__}
        self._update_worker: UpdateCheckWorker | None = None
        self._load_prompts()
        # Verificação de sessão no startup, deferida para o event loop (não bloqueia).
        QTimer.singleShot(0, self._run_startup_auth_check)
        # Polling do mini-player, também deferido para não atrasar o boot.
        QTimer.singleShot(0, self._start_music_worker)
        # Discord Rich Presence (best-effort), deferido para fora do boot.
        QTimer.singleShot(0, lambda: self._update_presence("idle"))
        # Verificação de atualização (best-effort), deferida para fora do boot.
        QTimer.singleShot(0, self._run_startup_update_check)

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

    @Property(str, constant=True)
    def structureInstruction(self) -> str:
        # Instrução fixa de estrutura sempre injetada no prompt final.
        # Exibida read-only no editor; não muda em runtime (constant=True).
        return STRUCTURE_INSTRUCTION

    @Property(str, notify=pipelinePhaseChanged)
    def pipelinePhase(self) -> str:
        return self._pipeline_phase

    @Property(str, notify=backendLabelChanged)
    def backendLabel(self) -> str:
        # Rótulo do backend configurado (NotebookLM / Gemini / Ollama).
        return self._backend_label

    @Property(str, constant=True)
    def appVersion(self) -> str:
        # Versão empacotada (kairos.__version__); não muda em runtime.
        return __version__

    @Property(bool, notify=updateInfoChanged)
    def updateAvailable(self) -> bool:
        return self._update_info["available"]

    @Property(str, notify=updateInfoChanged)
    def updateVersion(self) -> str:
        return self._update_info["version"]

    @Property(str, notify=updateInfoChanged)
    def updateUrl(self) -> str:
        return self._update_info["url"]

    @Property(bool, notify=reduceMotionChanged)
    def reduceMotion(self) -> bool:
        return self._reduce_motion

    @Property(bool, notify=themeChanged)
    def darkMode(self) -> bool:
        return self._dark_mode

    @Property(int, notify=progressChanged)
    def progress(self) -> int:
        return self._progress

    @Property('QVariantMap', notify=graphChanged)
    def graphData(self) -> dict:
        # {"central", "central_path", "nodes": [{"label", "path"}]} ou {} (sem mapa).
        return self._graph_data

    @Property(str, notify=musicChanged)
    def musicStatus(self) -> str:
        return self._music["status"]

    @Property(str, notify=musicChanged)
    def musicTitle(self) -> str:
        return self._music["title"]

    @Property(str, notify=musicChanged)
    def musicArtist(self) -> str:
        return self._music["artist"]

    @Property(str, notify=musicChanged)
    def musicArtUrl(self) -> str:
        return self._music["artUrl"]

    @Property(bool, notify=musicChanged)
    def musicCanNext(self) -> bool:
        return self._music["canNext"]

    @Property(bool, notify=musicChanged)
    def musicCanPrev(self) -> bool:
        return self._music["canPrev"]

    @Property(bool, notify=musicChanged)
    def musicAvailable(self) -> bool:
        return self._music.get("available", False)

    # ── Internal helpers ───────────────────────────────────────────────────

    def _set_status(self, text: str, state: str = "idle") -> None:
        self._status_text = text
        self._status_state = state
        self.statusChanged.emit()

    def _set_can_process(self, value: bool) -> None:
        if self._can_process != value:
            self._can_process = value
            self.canProcessChanged.emit()

    # 4 fases de peso igual (25% cada). A fase ativa define o alvo; a barra na
    # UI interpola suavemente do valor anterior até ele. Fase de erro NÃO mexe no
    # progresso — a barra congela onde estava e muda de cor.
    _PHASE_PROGRESS = {
        "": 0,
        "extracting": 25,
        "processing": 75,
        "writing": 100,
        "done": 100,
    }

    def _set_phase(self, phase: str) -> None:
        if self._pipeline_phase != phase:
            self._pipeline_phase = phase
            self.pipelinePhaseChanged.emit()
        if phase in self._PHASE_PROGRESS:
            self._set_progress(self._PHASE_PROGRESS[phase])
        # Discord Rich Presence acompanha a fase (best-effort).
        self._update_presence(
            "processing" if phase in ("extracting", "processing", "writing") else "idle"
        )

    def _set_progress(self, value: int) -> None:
        if self._progress != value:
            self._progress = value
            self.progressChanged.emit()

    def _set_graph(self, data: dict) -> None:
        self._graph_data = data or {}
        self.graphChanged.emit()

    def _refresh_backend_label(self) -> None:
        backend = cfg.load().get("processor_backend", "notebooklm")
        label = _BACKEND_LABELS.get(backend, "NotebookLM")
        if label != self._backend_label:
            self._backend_label = label
            self.backendLabelChanged.emit()

    def _notify_failure(self, detail: str) -> None:
        from kairos.integrations import notifier
        notifier.notify("Kairos — falhou", detail)

    def _update_presence(self, kind: str) -> None:
        """Atualiza o Discord Rich Presence (best-effort, não bloqueia a GUI)."""
        from kairos.integrations import discord_presence
        if kind == "processing":
            theme = self._current_prompt_label or "material"
            discord_presence.set_state(f"Processando: {theme}", "Estudando com Kairos")
        else:  # idle / pronto
            discord_presence.set_state("Pronto para aprender", "Estudando com Kairos")

    def _start_music_worker(self) -> None:
        self._music_worker = MusicWorker()
        self._music_worker.updated.connect(self._on_music_update)
        self._music_worker.start()

    def _on_music_update(self, data: dict) -> None:
        worker = self.sender()
        if worker is not self._music_worker:
            return
        if data == self._music:
            return
        self._music = data
        self.musicChanged.emit()

    def _session_elapsed(self) -> float:
        if self._session_start is None:
            return 0.0
        return time.monotonic() - self._session_start


    def _load_prompts(self) -> None:
        prompts_raw = cfg.load_prompts()
        valid: list[dict] = []
        for p in prompts_raw:
            if not isinstance(p, dict):
                continue
            if "label" not in p or "text" not in p:
                continue
            if not p["label"].strip() or not p["text"].strip():
                continue
            valid.append(p)
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

    def _run_startup_update_check(self) -> None:
        """Checa o último release em background (best-effort, não bloqueia)."""
        self._update_worker = UpdateCheckWorker()
        self._update_worker.finished.connect(self._on_update_check_finished)
        self._update_worker.start()

    def _on_update_check_finished(self, info: dict) -> None:
        worker = self.sender()
        if worker is not self._update_worker:
            return
        # try/except: se onAppClose já desconectou tudo (sem zerar a ref), um
        # finished tardio passa o guard e re-desconectaria sinal já solto.
        try:
            self._update_worker.finished.disconnect(self._on_update_check_finished)
        except (TypeError, RuntimeError):
            pass
        self._update_worker = None
        if not info.get("available"):
            return
        self._update_info = {
            "available": True,
            "version": info.get("version", ""),
            "url": info.get("url", ""),
            "current": __version__,
        }
        self.updateInfoChanged.emit()

    # ── Public slots ───────────────────────────────────────────────────────

    @Slot(str)
    def loadSource(self, source: str) -> None:
        source = source.strip()
        if not source:
            return
        self._set_graph({})  # nova fonte → mapa anterior some
        # Normaliza URI file:// para caminho local
        if source.startswith("file://"):
            source = QUrl(source).toLocalFile()
        is_youtube = "youtube.com" in source or "youtu.be" in source
        if is_youtube:
            self._loaded_source = source
            display = source if len(source) <= 52 else source[:49] + "..."
            self._set_status(f"Pronto: {display}", "idle")
            self._set_can_process(True)
        elif (
            Path(source).suffix.lower() == ".pdf"
            or Path(source).suffix.lower() in AUDIO_SUFFIXES
            or Path(source).suffix.lower() in TEXT_SUFFIXES
        ):
            path = Path(source)
            if not path.is_file():
                self._set_status("Arquivo não encontrado", "error")
                return
            self._loaded_source = source
            self._set_status(f"Pronto: {path.name}", "idle")
            self._set_can_process(True)
        else:
            self._set_status(
                "Fonte inválida — use um PDF, texto, áudio ou URL do YouTube", "error"
            )

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

        self._set_graph({})
        self._pipeline_source = self._loaded_source
        if prompt_index < 0 or prompt_index >= len(self._prompts):
            self._set_status("Erro: prompt não encontrado", "error")
            return
        self._current_prompt_label = self._prompts[prompt_index]["label"]

        self._set_can_process(False)
        is_youtube = self._pipeline_source.startswith("http")
        is_audio = not is_youtube and Path(self._pipeline_source).suffix.lower() in AUDIO_SUFFIXES
        self._set_status(
            "Buscando transcrição..." if is_youtube
            else "Transcrevendo áudio..." if is_audio
            else "Extraindo texto...",
            "running",
        )
        self._set_progress(0)  # zera antes da 1ª fase: barra anima de 0 → 25
        self._set_phase("extracting")
        self._session_start = time.monotonic()

        self._extraction_worker = ExtractionWorker(self._pipeline_source)
        self._extraction_worker.finished.connect(self._on_extraction_finished)
        self._extraction_worker.error.connect(self._on_extraction_error)
        self._extraction_worker.start()

    @Slot()
    def onAppClose(self) -> None:
        if self._music_worker is not None:
            try:
                self._music_worker.updated.disconnect(self._on_music_update)
            except (TypeError, RuntimeError):
                pass
            self._music_worker.stop()
            self._music_worker.wait(2000)
            if self._music_worker.isRunning():
                self._music_worker.terminate()
                self._music_worker.wait(1000)
            self._music_worker = None
        for worker in (
            self._extraction_worker,
            self._processor_worker,
            self._writer_worker,
            self._auth_worker,
            self._update_worker,
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
        from kairos.integrations import discord_presence
        discord_presence.shutdown()

    @Slot(result='QVariantMap')
    def getSettings(self) -> dict:
        config = cfg.load()
        return {
            "obsidian_vault_path": config.get("obsidian_vault_path", ""),
            "simpmusic_path": config.get("simpmusic_path", ""),
            "simpmusic_autostart": bool(config.get("simpmusic_autostart", True)),
            "music_playlist_url": config.get("music_playlist_url", ""),
            "reduce_motion": bool(config.get("reduce_motion", False)),
            "discord_presence": bool(config.get("discord_presence", False)),
            "discord_client_id": config.get("discord_client_id", ""),
            "processor_backend": config.get("processor_backend", "notebooklm"),
            "gemini_api_key": config.get("gemini_api_key", ""),
            "gemini_model": config.get("gemini_model", DEFAULT_CONFIG["gemini_model"]),
            "local_endpoint": config.get("local_endpoint", DEFAULT_CONFIG["local_endpoint"]),
            "prompts": cfg.load_prompts(),
        }

    @Slot('QVariantMap')
    def saveSettings(self, settings: dict) -> None:
        try:
            config = cfg.load()
            config["obsidian_vault_path"] = str(settings.get("obsidian_vault_path", "") or "")
            config["simpmusic_path"] = str(settings.get("simpmusic_path", "") or "")
            config["simpmusic_autostart"] = bool(settings.get("simpmusic_autostart", True))
            config["music_playlist_url"] = str(settings.get("music_playlist_url", "") or "").strip()
            new_reduce_motion = bool(settings.get("reduce_motion", False))
            config["reduce_motion"] = new_reduce_motion
            config["discord_presence"] = bool(settings.get("discord_presence", False))
            config["discord_client_id"] = str(settings.get("discord_client_id", "") or "").strip()
            backend = str(settings.get("processor_backend", "") or "notebooklm")
            config["processor_backend"] = (
                backend if backend in ("notebooklm", "gemini", "ollama") else "notebooklm"
            )
            config["gemini_api_key"] = str(settings.get("gemini_api_key", "") or "")
            config["gemini_model"] = (
                str(settings.get("gemini_model", "") or "").strip()
                or DEFAULT_CONFIG["gemini_model"]
            )
            config["local_endpoint"] = (
                str(settings.get("local_endpoint", "") or "").strip()
                or DEFAULT_CONFIG["local_endpoint"]
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
            if valid:
                cfg.save_prompts(valid)
            cfg.save(config)
            self._load_prompts()
            self._refresh_backend_label()
            if self._reduce_motion != new_reduce_motion:
                self._reduce_motion = new_reduce_motion
                self.reduceMotionChanged.emit()
            # Aplica o toggle do Discord na hora (liga/desliga sem reiniciar).
            self._update_presence(
                "processing"
                if self._pipeline_phase in ("extracting", "processing", "writing")
                else "idle"
            )
            self.settingsSaved.emit()
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")
            self.settingsError.emit(f"Erro ao salvar configurações: {e}")

    @Slot()
    def toggleTheme(self) -> None:
        # Alterna claro/escuro e persiste o modo em config.json.
        self._dark_mode = not self._dark_mode
        self.themeChanged.emit()
        try:
            config = cfg.load()
            config["dark_mode"] = self._dark_mode
            cfg.save(config)
        except Exception as e:
            logger.error(f"Erro ao salvar o tema: {e}")

    @Slot(str, bool, result=str)
    def browseForPath(self, current: str, is_directory: bool) -> str:
        start = current if current and Path(current).exists() else str(Path.home())
        if is_directory:
            path = QFileDialog.getExistingDirectory(None, "Selecionar pasta", start)
        else:
            path, _ = QFileDialog.getOpenFileName(None, "Selecionar arquivo", start)
        return path or ""

    @Slot(str)
    def openNote(self, note_path: str) -> None:
        """Abre a nota no Obsidian via obsidian://open?vault=&file=.

        Fallback para abrir o arquivo no app padrão se o caminho estiver fora do
        vault configurado.
        """
        if not note_path:
            return
        p = Path(note_path)
        vault_str = cfg.load().get("obsidian_vault_path", "")
        try:
            vault = Path(vault_str).expanduser()
            rel = p.relative_to(vault).as_posix()
            url = QUrl("obsidian://open")
            query = QUrlQuery()
            query.addQueryItem("vault", vault.name)
            query.addQueryItem("file", rel)
            url.setQuery(query)
        except (ValueError, OSError):
            url = QUrl.fromLocalFile(str(p))
        QDesktopServices.openUrl(url)

    @Slot()
    def openUpdatePage(self) -> None:
        """Abre a página do release no navegador padrão."""
        url = self._update_info.get("url", "")
        if url:
            QDesktopServices.openUrl(QUrl(url))

    @Slot()
    def dismissUpdate(self) -> None:
        """Esconde o banner de atualização (apenas nesta sessão)."""
        if not self._update_info["available"]:
            return
        self._update_info = {"available": False, "version": "", "url": "", "current": __version__}
        self.updateInfoChanged.emit()

    # ── Controles de música (Simpmusic via MPRIS) ──────────────────────────

    @Slot()
    def musicPlayPause(self) -> None:
        from kairos.integrations import music_mpris
        music_mpris.play_pause()

    @Slot()
    def musicNext(self) -> None:
        from kairos.integrations import music_mpris
        music_mpris.next()

    @Slot()
    def musicPrevious(self) -> None:
        from kairos.integrations import music_mpris
        music_mpris.previous()

    @Slot(int)
    def musicVolume(self, direction: int) -> None:
        from kairos.integrations import music_mpris
        music_mpris.volume_step(0.05 if direction >= 0 else -0.05)

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
            self._set_status("Erro: prompt não encontrado", "error")
            self._set_phase("error_extraction")
            self._set_can_process(True)
            return

        # Guarda o texto extraído: se o backend falhar, o usuário pode escolher
        # salvá-lo localmente (#pendente) a partir do diálogo de decisão.
        self._pending_text = text

        self._set_status(f"Conectando ao {self._backend_label}...", "running")
        self._set_phase("processing")
        self._processor_worker = ProcessorWorker(text, prompt_obj["text"])
        self._processor_worker.finished.connect(self._on_processing_finished)
        self._processor_worker.error.connect(self._on_processing_error)
        self._processor_worker.decision.connect(self._on_processing_decision)
        self._processor_worker.start()

    def _on_extraction_error(self, error_msg: str) -> None:
        worker = self.sender()
        if worker is not self._extraction_worker:
            return
        self._set_status(f"Erro: {error_msg}", "error")
        self._set_phase("error_extraction")
        self._set_can_process(True)
        self._notify_failure(error_msg)
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

    def _clear_processor_worker(self) -> None:
        if self._processor_worker is None:
            return
        for sig, slot in (
            (self._processor_worker.finished, self._on_processing_finished),
            (self._processor_worker.error, self._on_processing_error),
            (self._processor_worker.decision, self._on_processing_decision),
        ):
            try:
                sig.disconnect(slot)
            except (TypeError, RuntimeError):
                pass
        self._processor_worker = None

    def _on_processing_finished(self, result: str, mode: str) -> None:
        worker = self.sender()
        if worker is not self._processor_worker:
            return
        self._clear_processor_worker()
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
        self._clear_processor_worker()
        self._set_status(f"Erro no processamento: {error_msg}", "error")
        self._set_phase("error_processing")
        self._set_can_process(True)
        self._notify_failure(error_msg)
        log_session(
            source=self._pipeline_source or "",
            prompt_label=self._current_prompt_label or "",
            status="✗",
            duration_seconds=self._session_elapsed(),
            mode="local",
        )

    # Mapeia a categoria do ProcessorError para um título PT-BR do diálogo.
    _DECISION_TITLES = {
        "too_large": "Arquivo muito grande",
        "unavailable": "Backend de IA indisponível",
        "backend": "Falha no backend de IA",
    }

    def _on_processing_decision(self, category: str, message: str) -> None:
        worker = self.sender()
        if worker is not self._processor_worker:
            return
        self._clear_processor_worker()
        # Estado de erro visual (barra congela), mas mantém o texto pendente e
        # pede a decisão. Não cai em silêncio para local.
        self._set_phase("error_processing")
        self._set_status("Aguardando sua decisão...", "warning")
        title = self._DECISION_TITLES.get(category, "Falha no processamento")
        self.decisionNeeded.emit(title, message)

    @Slot()
    def saveLocally(self) -> None:
        """Salva o texto extraído como nota local com tag #pendente (fallback)."""
        if self._pending_text is None:
            self.cancelProcessing()
            return
        from kairos.pipeline.processor import build_fallback
        result = build_fallback(self._pending_text)
        self._pending_text = None
        self._current_mode = "fallback"
        self._set_status("Salvando localmente...", "running")
        self._set_phase("writing")
        self._writer_worker = WriterWorker(
            result,
            self._pipeline_source,
            self._current_prompt_label or "",
            "fallback",
            session_duration=_fmt_duration(self._session_elapsed()),
        )
        self._writer_worker.finished.connect(self._on_write_finished)
        self._writer_worker.error.connect(self._on_write_error)
        self._writer_worker.start()

    @Slot()
    def cancelProcessing(self) -> None:
        """Descarta o estado e volta à DropZone."""
        self._pending_text = None
        self._set_progress(0)
        self._set_phase("")
        self._set_status("Pronto", "idle")
        self._set_can_process(True)
        self._update_presence("idle")

    def _on_write_finished(self, path: str, graph: dict) -> None:
        worker = self.sender()
        if worker is not self._writer_worker:
            return
        elapsed = self._session_elapsed()
        filename = escape(Path(path).name)
        uri = Path(path).as_uri()
        link = f'<a href="{uri}">{filename}</a>'
        from kairos.integrations import notifier
        if self._current_mode == "fallback":
            self._set_status(
                f"⚠ Salvo localmente — backend de IA indisponível: {link}",
                "warning",
            )
            notifier.notify("Kairos — salvo localmente", f"{Path(path).name} (backend de IA indisponível)")
        else:
            self._set_status(f"Nota salva: {link}", "success")
            notifier.notify("Kairos — nota pronta", Path(path).name)
        self._set_graph(graph)
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
        elapsed = self._session_elapsed()
        self._set_status(error_msg, "error")
        self._set_phase("error_writing")
        self._set_can_process(True)
        self._notify_failure(error_msg)
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
