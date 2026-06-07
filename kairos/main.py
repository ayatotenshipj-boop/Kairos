import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from kairos.integrations import launcher
from kairos.ui.main_window import MainWindow


def main():
    """Ponto de entrada da aplicação Kairos."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Kairos")

    styles_path = Path(__file__).parent / "ui" / "styles.qss"
    if styles_path.exists():
        app.setStyleSheet(styles_path.read_text(encoding="utf-8"))

    window = MainWindow()
    window.show()

    launcher.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()