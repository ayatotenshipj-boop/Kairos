from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFileDialog, QLabel

DEFAULT_TEXT = "Arraste um PDF\nou cole uma URL do YouTube"
INVALID_RESET_MS = 2000


class DropZone(QLabel):
    """Área de drop/clique para carregar um PDF.

    Emite file_loaded(str) com o caminho completo quando um PDF válido
    é solto ou selecionado. Toda a sinalização de estado é feita via
    objectName (lido pelo styles.qss), nunca por setStyleSheet inline.
    """

    file_loaded = Signal(str)

    def __init__(self, parent=None):
        super().__init__(DEFAULT_TEXT, parent)
        self.setObjectName("dropZone")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(160)
        self.setAcceptDrops(True)

    def _set_state(self, state):
        """Troca o objectName para o estado visual e reaplica o estilo."""
        self.setObjectName(state)
        style = self.style()
        style.unpolish(self)
        style.polish(self)

    def _reset_state(self):
        self.setText(DEFAULT_TEXT)
        self._set_state("dropZone")

    def _show_invalid(self):
        self._set_state("dropZoneInvalid")
        QTimer.singleShot(INVALID_RESET_MS, self._reset_state)

    def _accept(self, path):
        self.setText(path.name)
        self._set_state("dropZoneActive")
        self.file_loaded.emit(str(path))

    def _accept_url(self, url_str: str):
        display = url_str if len(url_str) <= 42 else url_str[:39] + "..."
        self.setText(display)
        self._set_state("dropZoneActive")
        self.file_loaded.emit(url_str)

    @staticmethod
    def _is_pdf(path):
        return path.is_file() and path.suffix.lower() == ".pdf"

    @staticmethod
    def _is_youtube_url(url_str: str) -> bool:
        return "youtube.com" in url_str or "youtu.be" in url_str

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            self._show_invalid()
            return

        local_path = urls[0].toLocalFile()
        url_str = urls[0].toString()

        if local_path:
            path = Path(local_path)
            if self._is_pdf(path):
                self._accept(path)
                event.acceptProposedAction()
            else:
                self._show_invalid()
                event.ignore()
        elif self._is_youtube_url(url_str):
            self._accept_url(url_str)
            event.acceptProposedAction()
        else:
            self._show_invalid()
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione um PDF",
            "",
            "Arquivos PDF (*.pdf)",
        )
        if not selected:
            return
        path = Path(selected)
        if self._is_pdf(path):
            self._accept(path)
        else:
            self._show_invalid()
