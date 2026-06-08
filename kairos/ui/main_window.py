import logging
import time
from datetime import datetime
from html import escape
from pathlib import Path

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from hypothesis import event

from kairos.config import config as cfg
from kairos.config.defaults import DEFAULT_CONFIG
from kairos.pipeline.ingestor import ingest
from kairos.pipeline.logger import log_session
from kairos.pipeline.processor import process
from kairos.pipeline.writer import write as write_note
from kairos.ui.drop_zone import DropZone

logger = logging.getLogger(__name__)


def _fmt_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    m, s = divmod(total, 60)
    return f"{m}m{s:02d}s"


class ExtractionWorker(QThread):
    """Thread worker para extrair texto de PDF ou YouTube sem travar a UI."""

    finished = Signal(str)  # emitido com o texto extraído
    error = Signal(str)  # emitido com mensagem de erro amigável

    def __init__(self, source: str):
        super().__init__()
        self.source = source

    def run(self):
        try:
            text, _source_type = ingest(self.source)
            self.finished.emit(text)
        except FileNotFoundError:
            self.error.emit("Arquivo não encontrado")
        except ValueError as e:
            self.error.emit(str(e))
        except RuntimeError as e:
            self.error.emit(str(e))
        except Exception as e:
            logger.exception(f"Erro inesperado ao processar {self.source}")
            self.error.emit(f"Erro inesperado: {e}")


class ProcessorWorker(QThread):
    """Thread worker para processar texto via NotebookLM sem travar a UI."""

    finished = Signal(str, str)  # emitido com (resultado, modo)
    error = Signal(str)  # emitido com mensagem de erro amigável

    def __init__(self, text: str, prompt_text: str):
        super().__init__()
        self.text = text
        self.prompt_text = prompt_text

    def run(self):
        try:
            result, mode = process(self.text, self.prompt_text)
            self.finished.emit(result, mode)
        except Exception as e:
            logger.exception("Erro inesperado no processamento")
            self.error.emit(f"Erro inesperado: {e}")


class WriterWorker(QThread):
    """Thread worker para salvar a nota no Obsidian sem travar a UI."""

    finished = Signal(str)  # emitido com o caminho completo da nota salva
    error = Signal(str)  # emitido com mensagem de erro em PT-BR

    def __init__(self, result: str, source_path: str, prompt_label: str, mode: str, session_duration: str = ""):
        super().__init__()
        self.result = result
        self.source_path = source_path
        self.prompt_label = prompt_label
        self.mode = mode
        self.session_duration = session_duration

    def run(self):
        try:
            path = write_note(self.result, self.source_path, self.prompt_label, self.mode, session_duration=self.session_duration)
            self.finished.emit(path)
        except ValueError as e:
            if "não configurado" in str(e):
                self.error.emit("Configure o vault do Obsidian nas configurações")
            else:
                self.error.emit(str(e))
        except RuntimeError as e:
            self.error.emit(str(e))
        except Exception as e:
            logger.exception("Erro inesperado ao salvar nota")
            self.error.emit(f"Erro inesperado ao salvar: {e}")


class MainWindow(QMainWindow):
    """Janela principal da aplicação Kairos."""

    def __init__(self):
        super().__init__()
        self._loaded_file = None
        self._extracted_text = None
        self._current_prompt_label = None
        self._current_mode: str = "notebooklm"
        self._session_start: float | None = None
        self._extraction_worker = None
        self._processor_worker = None
        self._writer_worker = None
        self._prompts: list[dict] = []
        # Captura imutável do source no início do pipeline
        self._pipeline_source: str | None = None
        self._setup_ui()
        self._load_prompts()

    def _setup_ui(self):
        """Configura a interface da janela."""
        self.setWindowTitle("Kairos")
        self.resize(960, 640)
        self.setMinimumSize(800, 500)

        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_main_panel(), 1)

        self.setCentralWidget(central)

    def _build_sidebar(self):
        """Painel esquerdo: identidade, sessão atual e log recente."""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("KAIROS")
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)

        layout.addWidget(self._build_separator())

        session_header = QLabel("Sessão atual")
        session_header.setObjectName("sidebarHeader")
        layout.addWidget(session_header)

        session_date = QLabel(datetime.now().strftime("%d/%m/%Y"))
        layout.addWidget(session_date)

        layout.addWidget(self._build_separator())

        log_header = QLabel("Log recente")
        log_header.setObjectName("sidebarHeader")
        layout.addWidget(log_header)

        layout.addStretch()

        config_btn = QPushButton("⚙ Config")
        config_btn.setObjectName("configButton")
        config_btn.clicked.connect(self._open_settings)
        layout.addWidget(config_btn)

        return sidebar

    def _build_main_panel(self):
        """Painel direito: drop zone, prompt, botão e status."""
        panel = QWidget()
        panel.setObjectName("mainPanel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.drop_zone = DropZone()
        self.drop_zone.file_loaded.connect(self._on_file_loaded)
        layout.addWidget(self.drop_zone)

        self.url_input = QLineEdit()
        self.url_input.setObjectName("urlInput")
        self.url_input.setPlaceholderText("Cole uma URL do YouTube e pressione Enter...")
        self.url_input.returnPressed.connect(self._on_url_submitted)
        layout.addWidget(self.url_input)

        prompt_label = QLabel("Prompt:")
        prompt_label.setObjectName("sidebarHeader")
        layout.addWidget(prompt_label)

        self.prompt_selector = QComboBox()
        layout.addWidget(self.prompt_selector)

        self.process_button = QPushButton("▶ Processar")
        self.process_button.setObjectName("processButton")
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self._on_process_clicked)
        layout.addWidget(self.process_button)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setTextFormat(Qt.TextFormat.RichText)
        self.status_label.setOpenExternalLinks(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

        return panel

    def _on_url_submitted(self):
        """Valida e carrega uma URL do YouTube digitada/colada no campo de texto."""
        url = self.url_input.text().strip()
        if not url:
            return
        if "youtube.com" not in url and "youtu.be" not in url:
            self.status_label.setText("URL inválida — cole um link do YouTube")
            return
        self.url_input.clear()
        self._on_file_loaded(url)

    def _on_file_loaded(self, source: str):
        """Guarda a fonte (path ou URL), habilita o processamento e atualiza o status."""
        self._loaded_file = source
        # Só habilita botão se nenhum worker estiver ativo
        any_worker_running = any(
            w is not None and w.isRunning()
            for w in (self._extraction_worker, self._processor_worker, self._writer_worker)
        )
        if not any_worker_running:
            self.process_button.setEnabled(True)
        if source.startswith("http"):
            display = source if len(source) <= 52 else source[:49] + "..."
            self.status_label.setText(f"Pronto: {display}")
        else:
            self.status_label.setText(f"Pronto: {Path(source).name}")

    def _on_process_clicked(self):
        """Dispara a extração de texto do PDF em background."""
        if not self._loaded_file:
            self.status_label.setText("Erro: nenhum arquivo carregado")
            return

  # Previne race condition: não inicia novo worker se já houver um rodando
        if self._extraction_worker is not None and self._extraction_worker.isRunning():
            return
        if self._processor_worker is not None and self._processor_worker.isRunning():
            return
        if self._writer_worker is not None and self._writer_worker.isRunning():
            return

# Captura source e prompt imutáveis no início do pipeline
        self._pipeline_source = self._loaded_file
        selected_label = self.prompt_selector.currentText()
        prompt_obj = next(
            (p for p in self._prompts if p["label"] == selected_label),
            None,
        )
        if not prompt_obj:
            self.status_label.setText("Erro: prompt não encontrado")
            return
        self._current_prompt_label = selected_label

        self.process_button.setEnabled(False)
        is_youtube = self._pipeline_source.startswith("http")
        self.status_label.setText(
            "Buscando transcrição..." if is_youtube else "Extraindo texto..."
        )
        self._session_start = time.monotonic()

        self._extraction_worker = ExtractionWorker(self._pipeline_source)
        self._extraction_worker.finished.connect(self._on_extraction_finished)
        self._extraction_worker.error.connect(self._on_extraction_error)
        self._extraction_worker.start()

    def _on_extraction_finished(self, text: str):
        """Chamado quando a extração termina — dispara o processamento."""
        # Proteção contra race condition: ignora callbacks de workers antigos
        worker = self.sender()
        if worker is not self._extraction_worker:
            return

        self._extracted_text = text
        self._extraction_worker.finished.disconnect(self._on_extraction_finished)
        self._extraction_worker.error.disconnect(self._on_extraction_error)
        self._extraction_worker = None

        # Usa o prompt capturado no início do pipeline
        prompt_obj = next(
            (p for p in self._prompts if p["label"] == self._current_prompt_label),
            None,
        )
        if not prompt_obj:
            self.status_label.setText("Erro: prompt não encontrado")
            self.process_button.setEnabled(True)
            return

        prompt_text = prompt_obj["text"]

        # Dispara o processamento
        self.status_label.setText("Conectando ao NotebookLM...")
        self._processor_worker = ProcessorWorker(text, prompt_text)
        self._processor_worker.finished.connect(self._on_processing_finished)
        self._processor_worker.error.connect(self._on_processing_error)
        self._processor_worker.start()

    def _on_extraction_error(self, error_msg: str):
        """Chamado quando a extração falha."""
        # Proteção contra race condition: ignora callbacks de workers antigos
        worker = self.sender()
        if worker is not self._extraction_worker:
            return

        self.status_label.setText(f"Erro: {error_msg}")
        self.process_button.setEnabled(True)
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

    def _on_processing_finished(self, result: str, mode: str):
        """Chamado quando o processamento termina — dispara a escrita da nota."""
        # Proteção contra race condition: ignora callbacks de workers antigos
        worker = self.sender()
        if worker is not self._processor_worker:
            return

        self._processor_worker.finished.disconnect(self._on_processing_finished)
        self._processor_worker.error.disconnect(self._on_processing_error)
        self._processor_worker = None
        self._current_mode = mode
        self.status_label.setText("Salvando nota no Obsidian...")

        self._writer_worker = WriterWorker(
            result, self._pipeline_source, self._current_prompt_label or "", mode,
            session_duration=_fmt_duration(self._session_elapsed()),
        )
        self._writer_worker.finished.connect(self._on_write_finished)
        self._writer_worker.error.connect(self._on_write_error)
        self._writer_worker.start()

    def _on_processing_error(self, error_msg: str):
        """Chamado quando o processamento falha."""
        # Proteção contra race condition: ignora callbacks de workers antigos
        worker = self.sender()
        if worker is not self._processor_worker:
            return

        self.status_label.setText(f"Erro no processamento: {error_msg}")
        self.process_button.setEnabled(True)
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

    def _session_elapsed(self) -> float:
        if self._session_start is None:
            return 0.0
        return time.monotonic() - self._session_start

    def _on_write_finished(self, path: str):
        """Chamado quando a nota é salva — exibe caminho clicável."""
        # Proteção contra race condition: ignora callbacks de workers antigos
        worker = self.sender()
        if worker is not self._writer_worker:
            return

        elapsed = self._session_elapsed()
        filename = escape(Path(path).name)
        uri = Path(path).as_uri()
        link = f'<a href="{uri}" style="color: #4a9eff;">{filename}</a>'

        if self._current_mode == "local":
            self.status_label.setText(
                f'⚠ Salvo localmente — NotebookLM indisponível: {link}'
            )
        else:
            self.status_label.setText(f'Nota salva: {link}')

        self.process_button.setEnabled(True)
        self._writer_worker.finished.disconnect(self._on_write_finished)
        self._writer_worker.error.disconnect(self._on_write_error)
        self._writer_worker = None
        log_session(
            source=self._pipeline_source or "",
            prompt_label=self._current_prompt_label or "",
            status="✓" if self._current_mode == "notebooklm" else "⚠ local",
            duration_seconds=elapsed,
            mode=self._current_mode,
        )

    def _on_write_error(self, error_msg: str):
        """Chamado quando a escrita da nota falha."""
        # Proteção contra race condition: ignora callbacks de workers antigos
        worker = self.sender()
        if worker is not self._writer_worker:
            return

        elapsed = self._session_elapsed()
        self.status_label.setText(error_msg)
        self.process_button.setEnabled(True)
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

    def _load_prompts(self):
        """Recarrega prompts do config e atualiza o QComboBox."""
        config = cfg.load()
        prompts_raw = config.get("prompts", DEFAULT_CONFIG["prompts"])

        # Valida e filtra prompts malformados
        valid_prompts = []
        for p in prompts_raw:
            # Verifica se prompt tem campos obrigatórios
            if not isinstance(p, dict):
                logger.warning(f"Prompt inválido (não é dict): {p}")
                continue
            if "label" not in p or "text" not in p:
                logger.warning(f"Prompt sem campos obrigatórios ('label' ou 'text'): {p}")
                continue
            if not p["label"].strip() or not p["text"].strip():
                logger.warning(f"Prompt com campos vazios: {p}")
                continue
            valid_prompts.append(p)

        # Se nenhum prompt válido, usa padrões
        if not valid_prompts:
            logger.error("Nenhum prompt válido encontrado, usando prompts padrão")
            valid_prompts = DEFAULT_CONFIG["prompts"]

        self._prompts = valid_prompts
        current = self.prompt_selector.currentText()
        self.prompt_selector.clear()
        for p in self._prompts:
            self.prompt_selector.addItem(p["label"])
        # Tenta preservar a seleção anterior
        idx = self.prompt_selector.findText(current)
        if idx >= 0:
            self.prompt_selector.setCurrentIndex(idx)

    def _open_settings(self):
        """Abre o dialog de configurações e recarrega prompts se salvo."""
        from kairos.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_prompts()

    def closeEvent(self, event):
        for worker in (self._extraction_worker, self._processor_worker, self._writer_worker):
            if worker is not None and worker.isRunning():
                try:
                    worker.finished.disconnect()
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
        super().closeEvent(event)

    def _build_separator(self):
        """Linha horizontal divisória."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setObjectName("separator")
        return separator
