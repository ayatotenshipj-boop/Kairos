import logging
import multiprocessing
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from kairos.config import config as cfg
from kairos.integrations import launcher
from kairos.ui.backend import Backend

# Paletas dos diálogos Qt Widgets (QFileDialog, caixas de mensagem). Espelham os
# tokens do Theme.qml — sem elas, o Qt usa a paleta clara padrão (texto branco
# sobre fundo branco). A escolha segue config['dark_mode']. Fase 6 consolida o
# tema; aqui é o mínimo para legibilidade nos diálogos nativos.
_DARK_PALETTE = {
    "window":        "#0a0c10",  # bgBase
    "base":          "#0d111a",  # bgInput
    "alt_base":      "#171c28",  # bgElevated
    "button":        "#171c28",  # bgElevated
    "tooltip_bg":    "#171c28",  # bgElevated
    "text":          "#e2e6f0",  # textPrimary
    "text_dim":      "#7c899e",  # textSecondary
    "text_disabled": "#2a3040",  # textDisabled
    "accent":        "#e8903c",  # accentDefault
    "on_accent":     "#0a0c10",  # textOnAccent
}

# Tokens [data-theme="light"] do Theme.qml.
_LIGHT_PALETTE = {
    "window":        "#f4f1ea",  # bgBase
    "base":          "#ffffff",  # bgInput
    "alt_base":      "#fdfbf7",  # bgSurface
    "button":        "#fdfbf7",  # bgSurface
    "tooltip_bg":    "#ffffff",  # bgElevated
    "text":          "#2a2823",  # textPrimary
    "text_dim":      "#6b6760",  # textSecondary
    "text_disabled": "#9b968c",  # textDisabled
    "accent":        "#cc7a14",  # accentDefault
    "on_accent":     "#fffdf9",  # textOnAccent
}


def _apply_palette(app: QApplication, pal: dict) -> None:
    app.setStyle("Fusion")
    p = QPalette()
    window = QColor(pal["window"])
    base = QColor(pal["base"])
    text = QColor(pal["text"])
    button = QColor(pal["button"])
    accent = QColor(pal["accent"])
    disabled = QColor(pal["text_disabled"])

    p.setColor(QPalette.Window, window)
    p.setColor(QPalette.WindowText, text)
    p.setColor(QPalette.Base, base)
    p.setColor(QPalette.AlternateBase, QColor(pal["alt_base"]))
    p.setColor(QPalette.Text, text)
    p.setColor(QPalette.PlaceholderText, QColor(pal["text_dim"]))
    p.setColor(QPalette.Button, button)
    p.setColor(QPalette.ButtonText, text)
    p.setColor(QPalette.ToolTipBase, QColor(pal["tooltip_bg"]))
    p.setColor(QPalette.ToolTipText, text)
    p.setColor(QPalette.Highlight, accent)
    p.setColor(QPalette.HighlightedText, QColor(pal["on_accent"]))
    for role in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        p.setColor(QPalette.Disabled, role, disabled)
    app.setPalette(p)


def main():
    # Necessário para multiprocessing spawn no binário Nuitka onefile
    # (processamento NotebookLM roda isolado em subprocesso).
    multiprocessing.freeze_support()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # QApplication (não QGuiApplication) — necessário para QFileDialog em browseForPath
    app = QApplication(sys.argv)
    app.setApplicationName("Kairos")
    # Ícone da aplicação (janela, barra de tarefas, diálogos). Carrega vários
    # tamanhos para o Qt escolher o melhor por contexto.
    _icon = QIcon()
    _images = Path(__file__).parent / "images"
    if sys.platform == "win32":
        _ico = _images / "kairos_windows.ico"
        if _ico.is_file():
            _icon = QIcon(str(_ico))
    else:
        for _size in (16, 24, 32, 48, 64, 128, 256, 512):
            _png = _images / f"kairos_linux_{_size}x{_size}.png"
            if _png.is_file():
                _icon.addFile(str(_png))
    if not _icon.isNull():
        app.setWindowIcon(_icon)
    dark_mode = bool(cfg.load().get("dark_mode", True))
    _apply_palette(app, _DARK_PALETTE if dark_mode else _LIGHT_PALETTE)

    engine = QQmlApplicationEngine()
    # parent=app → CppOwnership: impede o GC do motor JS de coletar o wrapper
    # QML de `backend` durante a troca de fase (some toda a UI quando animado).
    backend = Backend(app)
    engine.rootContext().setContextProperty("backend", backend)

    qml_main = Path(__file__).parent / "ui" / "qml" / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_main)))

    if not engine.rootObjects():
        logging.error("Falha ao carregar main.qml")
        sys.exit(1)

    app.aboutToQuit.connect(backend.onAppClose)
    launcher.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()