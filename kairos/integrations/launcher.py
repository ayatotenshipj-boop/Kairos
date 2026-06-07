import logging
import subprocess
from pathlib import Path

from kairos.config import config as cfg

logger = logging.getLogger(__name__)

_process: subprocess.Popen | None = None


def start() -> None:
    global _process
    config = cfg.load()

    if not config.get("simpmusic_autostart", True):
        return

    path_str = (config.get("simpmusic_path") or "").strip()
    if not path_str:
        logger.warning("simpmusic_path não configurado — Simpmusic não será iniciado")
        return

    path = Path(path_str)
    if not path.exists():
        logger.error(f"Simpmusic não encontrado no caminho configurado: {path}")
        return

    try:
        _process = subprocess.Popen([str(path)])
        logger.info(f"Simpmusic iniciado (PID {_process.pid})")
    except Exception as e:
        logger.error(f"Erro ao iniciar Simpmusic: {e}")


def stop() -> None:
    global _process
    if _process is None:
        return
    if _process.poll() is not None:
        _process = None
        return
    try:
        _process.terminate()
        try:
            _process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _process.kill()
    except Exception as e:
        logger.error(f"Erro ao encerrar Simpmusic: {e}")
    finally:
        _process = None


def is_running() -> bool:
    return _process is not None and _process.poll() is None
