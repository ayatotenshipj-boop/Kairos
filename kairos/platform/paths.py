"""Caminhos de dados e configuração por plataforma.

Fonte única da verdade para diretórios do sistema. Nenhum outro módulo
usa Path.home() / '.config' diretamente.
"""
import sys
from pathlib import Path


def config_dir() -> Path:
    """Retorna o diretório de configuração da aplicação.

    Linux/macOS : ~/.config/kairos
    Windows     : %APPDATA%/kairos
    """
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Roaming"
    else:
        base = Path.home() / ".config"
    return base / "kairos"


def data_dir() -> Path:
    """Retorna o diretório de dados da aplicação.

    Linux/macOS : ~/.local/share/kairos
    Windows     : %APPDATA%/kairos/data
    """
    if sys.platform == "win32":
        return config_dir() / "data"
    return Path.home() / ".local" / "share" / "kairos"


def notebooklm_dir() -> Path:
    """Diretório padrão de dados do notebooklm-py.

    Linux/macOS : ~/.notebooklm
    Windows     : %APPDATA%/notebooklm
    """
    if sys.platform == "win32":
        return Path.home() / "AppData" / "Roaming" / "notebooklm"
    return Path.home() / ".notebooklm"
