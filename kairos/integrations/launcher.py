import logging
import subprocess
import threading
from pathlib import Path

from kairos.config import config as cfg

logger = logging.getLogger(__name__)

_process: subprocess.Popen | None = None
_lock = threading.Lock()


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

    with _lock:
        try:
            _process = subprocess.Popen([str(path)])
            logger.info(f"Simpmusic iniciado (PID {_process.pid})")
        except Exception as e:
            logger.error(f"Erro ao iniciar Simpmusic: {e}")


def stop() -> None:
    global _process
    with _lock:
        if _process is None:
            return
        if _process.poll() is not None:
            _process = None
            return
        try:
            # Solicita término gracioso sem bloquear
            _process.terminate()
            # Tenta kill imediato se ainda estiver rodando
            # poll() retorna None se processo ainda ativo
            if _process.poll() is None:
                _process.kill()
            # Sistema operacional limpa processo zombie
        except Exception as e:
            logger.error(f"Erro ao encerrar Simpmusic: {e}")
        finally:
            _process = None


def is_running() -> bool:
    with _lock:
        return _process is not None and _process.poll() is None
