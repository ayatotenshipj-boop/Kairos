import logging

from PySide6.QtCore import QThread, Signal

from kairos.pipeline.ingestor import ingest
from kairos.pipeline.processor import process
from kairos.pipeline.writer import write as write_note

logger = logging.getLogger(__name__)


def _fmt_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    m, s = divmod(total, 60)
    return f"{m}m{s:02d}s"


class ExtractionWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

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
    finished = Signal(str, str)
    error = Signal(str)

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


class AuthCheckWorker(QThread):
    """Verifica a sessão do NotebookLM sem bloquear a UI.

    A função auth_check já devolve (ok, mensagem_ptbr) e nunca lança, então não
    há sinal de erro separado.
    """
    finished = Signal(bool, str)

    def run(self):
        from kairos.integrations import notebooklm_client
        try:
            ok, msg = notebooklm_client.auth_check(test_network=False)
            self.finished.emit(ok, msg)
        except Exception as e:
            logger.exception("Erro inesperado na verificação de sessão do NotebookLM")
            self.finished.emit(False, f"Não foi possível verificar a sessão: {e}")


class WriterWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, result: str, source_path: str, prompt_label: str, mode: str, session_duration: str = ""):
        super().__init__()
        self.result = result
        self.source_path = source_path
        self.prompt_label = prompt_label
        self.mode = mode
        self.session_duration = session_duration

    def run(self):
        try:
            path = write_note(
                self.result, self.source_path, self.prompt_label,
                self.mode, session_duration=self.session_duration,
            )
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
