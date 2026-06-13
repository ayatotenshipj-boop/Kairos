"""Backend de controle de mídia por plataforma.

Linux   : playerctl + gdbus + pactl (implementado em integrations/music_mpris.py)
Windows : stub — available=False (SMTC a implementar futuramente)
macOS   : stub — available=False (MediaRemote a implementar futuramente)
"""
import shutil
import sys

_EMPTY = {
    "status": "Stopped", "title": "", "artist": "",
    "artUrl": "", "canNext": False, "canPrev": False,
    "available": False,
}


def is_supported() -> bool:
    """True apenas em Linux com playerctl disponível."""
    if sys.platform != "linux":
        return False
    return shutil.which("playerctl") is not None


def empty_snapshot() -> dict:
    return dict(_EMPTY)
