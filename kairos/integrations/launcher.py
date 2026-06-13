import logging
import os
import shutil
import subprocess
import sys
import threading
import time
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

# Janela máxima de espera pelo SimpMusic registrar no MPRIS antes de entregar a
# playlist, e intervalo de polling desse registro (launch em 2 fases).
_DELIVER_TIMEOUT_S = 20.0
_DELIVER_POLL_S = 0.5


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
    dividir a tela. Best-effort: no-op fora do Linux/Hyprland ou sem hyprctl."""
    if sys.platform != "linux":
        return
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


def _deliver_playlist(path: Path, url: str) -> None:
    """Entrega a playlist (deep-link) ao SimpMusic JÁ em execução.

    Passar a URL como argumento no cold start causa corrida: o deep-link chega
    antes da stack de rede do player subir (okhttp 'executor rejected' + dislike
    API 400 → dialog 'Unexpected Error'). Espera o player registrar no MPRIS e só
    então entrega numa 2ª invocação single-instance — sem corrida. Best-effort:
    no-op se o player não registrar a tempo."""
    deadline = time.monotonic() + _DELIVER_TIMEOUT_S
    while time.monotonic() < deadline:
        if _already_running():
            try:
                # 2ª invocação: o SimpMusic é single-instance e encaminha o
                # deep-link à instância viva, então este processo sai rápido.
                subprocess.run(
                    [str(path), url],
                    timeout=10, check=False,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                logger.info("Playlist entregue ao SimpMusic via deep-link")
            except Exception as e:
                logger.error(f"Erro ao entregar playlist ao SimpMusic: {e}")
            return
        time.sleep(_DELIVER_POLL_S)
    logger.warning("SimpMusic não registrou no MPRIS a tempo — playlist não entregue")


def start() -> None:
    global _process
    if sys.platform != "linux":
        logger.info("Launcher do SimpMusic disponível apenas no Linux — ignorado")
        return
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

    # Cold start SEM a playlist: passar o deep-link como argumento no lançamento
    # inicial causa corrida (o player recebe a URI antes da stack de rede subir).
    # A playlist é entregue depois, numa 2ª invocação, por _deliver_playlist.
    playlist_url = (config.get("music_playlist_url") or "").strip()

    with _lock:
        try:
            _process = subprocess.Popen([str(path)])
            logger.info(f"Simpmusic iniciado em segundo plano (PID {_process.pid})")
        except Exception as e:
            logger.error(f"Erro ao iniciar Simpmusic: {e}")
            return

    # Fase 2: entrega assíncrona da playlist quando o player estiver pronto.
    if playlist_url:
        threading.Thread(
            target=_deliver_playlist, args=(path, playlist_url), daemon=True
        ).start()


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
