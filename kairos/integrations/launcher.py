import logging
import os
import shutil
import subprocess
import threading
from pathlib import Path

from kairos.config import config as cfg

logger = logging.getLogger(__name__)

_process: subprocess.Popen | None = None
_lock = threading.Lock()

# Classe da janela do SimpMusic (StartupWMClass do .desktop) — usada nas
# windowrules do Hyprland para abrir o player em segundo plano.
_WM_CLASS = "com-maxrave-simpmusic-MainKt"
_MUSIC_WORKSPACE = "special:kairos-music"
# Nome do player no bus MPRIS (case-sensitive) — sinal autoritativo de instância.
_PLAYER = "SimpMusic"


def _already_running() -> bool:
    """True se já houver um SimpMusic registrado no MPRIS (instância
    controlável). Evita lançar uma segunda → dois players sobrepostos, e a faixa
    anterior demora a parar. O bus é sinal mais confiável que o nome do processo.
    """
    exe = shutil.which("playerctl")
    if not exe:
        return False
    try:
        result = subprocess.run(
            [exe, "-l"],
            timeout=2, check=False, capture_output=True, text=True,
        )
    except Exception:
        return False
    if result.returncode != 0:
        return False
    return any(line.strip() == _PLAYER for line in result.stdout.splitlines())


def _setup_background_rules() -> None:
    """No Hyprland, registra windowrules para o SimpMusic (e a janela de capa,
    mesma classe) abrir num workspace especial silencioso — segundo plano, sem
    dividir a tela. Best-effort: no-op fora do Hyprland ou sem hyprctl."""
    if not os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return
    exe = shutil.which("hyprctl")
    if not exe:
        return
    rules = (
        f"workspace {_MUSIC_WORKSPACE} silent, class:^({_WM_CLASS})$",
        f"float, class:^({_WM_CLASS})$",
    )
    for rule in rules:
        try:
            # windowrulev2: aceito no Hyprland atual (apenas aviso de deprecação,
            # capturado) e compatível com versões mais antigas.
            subprocess.run(
                [exe, "keyword", "windowrulev2", rule],
                timeout=2, check=False, capture_output=True, text=True,
            )
        except Exception as e:
            logger.warning(f"Erro ao registrar windowrule do SimpMusic: {e}")


def start() -> None:
    global _process
    config = cfg.load()

    if not config.get("simpmusic_autostart", True):
        return

    if _already_running():
        logger.info("SimpMusic já em execução — não será iniciado novamente")
        return

    path_str = (config.get("simpmusic_path") or "").strip()
    if not path_str:
        logger.warning("simpmusic_path não configurado — Simpmusic não será iniciado")
        return

    path = Path(path_str)
    if not path.exists():
        logger.error(f"Simpmusic não encontrado no caminho configurado: {path}")
        return

    # Registra as regras ANTES do launch para a janela já nascer em segundo plano.
    _setup_background_rules()

    # Playlist opcional: o SimpMusic aceita o deep link como argumento de linha de
    # comando no Linux. Vazio → abre normal.
    playlist_url = (config.get("music_playlist_url") or "").strip()
    cmd = [str(path), playlist_url] if playlist_url else [str(path)]

    with _lock:
        try:
            _process = subprocess.Popen(cmd)
            logger.info(f"Simpmusic iniciado em segundo plano (PID {_process.pid})")
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
            _process.terminate()
            try:
                _process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _process.kill()
        except Exception as e:
            logger.error(f"Erro ao encerrar Simpmusic: {e}")
        finally:
            _process = None
