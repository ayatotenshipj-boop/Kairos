import sys
from PySide6.QtWidgets import QApplication
from kairos.ui.main_window import MainWindow


def main():
    """Ponto de entrada da aplicação Kairos."""
    app = QApplication(sys.argv)
    app.setApplicationName("Kairos")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
