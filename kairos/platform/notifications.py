"""Backend de notificações de desktop por plataforma.

Linux   : notify-send (subprocess, best-effort)
Windows : plyer (se disponível), fallback MessageBeep não intrusivo
macOS   : osascript (subprocess, best-effort)

Nenhuma função levanta exceção — falha é sempre no-op.
"""
import logging
import shutil
import subprocess
import sys

logger = logging.getLogger(__name__)

_APP_NAME = "Kairos"


def _notify_linux(title: str, body: str) -> None:
    exe = shutil.which("notify-send")
    if not exe:
        logger.info("notify-send não encontrado — notificação de desktop indisponível")
        return
    try:
        subprocess.run([exe, "-a", _APP_NAME, title, body], timeout=5, check=False)
    except Exception as e:  # noqa: BLE001 — best-effort, nunca propaga
        logger.warning("notify-send falhou: %s", e)


def _notify_windows(title: str, body: str) -> None:
    try:
        from plyer import notification
        notification.notify(title=title, message=body, app_name=_APP_NAME, timeout=5)
        return
    except Exception:  # noqa: BLE001 — plyer ausente/indisponível
        pass
    try:
        import ctypes
        # Fallback mínimo: MessageBeep sem popup (não intrusivo)
        ctypes.windll.user32.MessageBeep(0)
    except Exception:  # noqa: BLE001
        pass


def _notify_macos(title: str, body: str) -> None:
    exe = shutil.which("osascript")
    if not exe:
        return
    script = (
        f'display notification "{body}" '
        f'with title "{title}" '
        f'sound name "Glass"'
    )
    try:
        subprocess.run([exe, "-e", script], timeout=5, check=False)
    except Exception as e:  # noqa: BLE001 — best-effort, nunca propaga
        logger.warning("osascript falhou: %s", e)


def notify(title: str, body: str = "") -> None:
    """Envia notificação de desktop. No-op em caso de falha."""
    if sys.platform == "linux":
        _notify_linux(title, body)
    elif sys.platform == "win32":
        _notify_windows(title, body)
    elif sys.platform == "darwin":
        _notify_macos(title, body)
