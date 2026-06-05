from PySide6.QtWidgets import QMainWindow
from pathlib import Path


class MainWindow(QMainWindow):
    """Janela principal da aplicação Kairos."""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_styles()

    def _setup_ui(self):
        """Configura a interface da janela."""
        self.setWindowTitle("Kairos")
        self.resize(960, 640)
        self.setMinimumSize(800, 500)

    def _load_styles(self):
        """Carrega o stylesheet QSS se existir."""
        styles_path = Path(__file__).parent / "styles.qss"
        if styles_path.exists():
            with open(styles_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
