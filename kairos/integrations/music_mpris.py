"""Controle e leitura do SimpMusic via MPRIS (playerctl) + volume via PipeWire.

Camada de integração pura — sem UI, sem lógica de negócio. Best-effort: nenhuma
função levanta exceção; falha vira no-op ou snapshot vazio. O alvo é sempre o
player **SimpMusic** (identity MPRIS, case-sensitive): `playerctl -p` distingue
maiúsculas, e `-p simpmusic` não casa com `org.mpris.MediaPlayer2.SimpMusic`.

Exceção: o SimpMusic **não** implementa a propriedade Volume do MPRIS (ignora
escritas), então `volume_step` controla o(s) stream(s) de áudio do app no
PipeWire/Pulse via `pactl`.
"""

import logging
import re
import shutil
import subprocess

logger = logging.getLogger(__name__)

# Identity MPRIS do SimpMusic. Case-sensitive — ver docstring do módulo.
PLAYER = "SimpMusic"
_BUS = f"org.mpris.MediaPlayer2.{PLAYER}"

# Separador improvável no conteúdo, usado no --format do snapshot.
_SEP = "\x1f"
_FORMAT = _SEP.join((
    "{{status}}",
    "{{xesam:title}}",
    "{{xesam:artist}}",
    "{{mpris:artUrl}}",
))

_EMPTY = {
    "status": "Stopped",
    "title": "",
    "artist": "",
    "artUrl": "",
    "canNext": False,
    "canPrev": False,
    "available": False,
}


def _run(*args: str) -> str | None:
    """Executa `playerctl -p SimpMusic <args>`. Retorna stdout (strip) ou None."""
    exe = shutil.which("playerctl")
    if not exe:
        logger.info("playerctl não encontrado — controle de mídia indisponível")
        return None
    try:
        result = subprocess.run(
            [exe, "-p", PLAYER, *args],
            timeout=2,
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        logger.warning(f"Erro ao executar playerctl: {e}")
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _can_flags() -> tuple[bool, bool]:
    """Lê CanGoNext/CanGoPrevious via gdbus (não expostos pelo --format do
    playerctl). Falha → (True, True): mantém os botões habilitados; um next/
    previous indisponível simplesmente vira no-op no player.
    """
    exe = shutil.which("gdbus")
    if not exe:
        return (True, True)
    try:
        result = subprocess.run(
            [
                exe, "call", "--session", "--dest", _BUS,
                "--object-path", "/org/mpris/MediaPlayer2",
                "--method", "org.freedesktop.DBus.Properties.GetAll",
                "org.mpris.MediaPlayer2.Player",
            ],
            timeout=2,
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        logger.warning(f"Erro ao ler capabilities via gdbus: {e}")
        return (True, True)
    if result.returncode != 0:
        return (True, True)

    def _flag(name: str) -> bool:
        m = re.search(rf"'{name}': <(true|false)>", result.stdout)
        return m.group(1) == "true" if m else True

    return (_flag("CanGoNext"), _flag("CanGoPrevious"))


def snapshot() -> dict:
    """Lê status + metadados + capabilities do SimpMusic.

    Retorna {"status","title","artist","artUrl","canNext","canPrev","available"}.
    `available` é True só quando o player responde via MPRIS; player ausente, sem
    playerctl, ou MPRIS sem resposta → _EMPTY com available=False (sem exceção, sem
    travar). No máximo 2 invocações de subprocess.
    """
    meta = _run("metadata", "--format", _FORMAT)
    if meta is None:
        return dict(_EMPTY)

    parts = meta.split(_SEP)
    parts += [""] * (4 - len(parts))
    status, title, artist, art_url = parts[:4]

    can_next, can_prev = _can_flags()

    return {
        "status": status or "Stopped",
        "title": title,
        "artist": artist,
        "artUrl": art_url,
        "canNext": can_next,
        "canPrev": can_prev,
        "available": True,
    }


def play_pause() -> None:
    _run("play-pause")


def next() -> None:
    _run("next")


def previous() -> None:
    _run("previous")


def _simpmusic_sink_inputs(listing: str) -> list[str]:
    """Extrai os índices de sink-input do SimpMusic da saída de `pactl list
    sink-inputs`. Consultado na hora — os índices são voláteis."""
    indexes: list[str] = []
    current: str | None = None
    for line in listing.splitlines():
        if line.startswith("Sink Input #"):
            current = line.split("#", 1)[1].strip()
        elif current and "application.name" in line and "simpmusic" in line.lower():
            indexes.append(current)
            current = None
    return indexes


def volume_step(delta: float) -> None:
    """Ajusta o volume do(s) stream(s) de áudio do SimpMusic via pactl.

    O SimpMusic não aceita volume por MPRIS, então o controle vai pelo stream no
    PipeWire/Pulse. Best-effort: no-op se pactl ausente ou sem stream ativo.
    """
    exe = shutil.which("pactl")
    if not exe:
        logger.info("pactl não encontrado — controle de volume indisponível")
        return
    try:
        listing = subprocess.run(
            [exe, "list", "sink-inputs"],
            timeout=2, check=False, capture_output=True, text=True,
        )
    except Exception as e:
        logger.warning(f"Erro ao listar streams de áudio: {e}")
        return
    if listing.returncode != 0:
        return

    indexes = _simpmusic_sink_inputs(listing.stdout)
    if not indexes:
        return

    pct = int(round(abs(delta) * 100))
    sign = "+" if delta >= 0 else "-"
    for idx in indexes:
        try:
            subprocess.run(
                [exe, "set-sink-input-volume", idx, f"{sign}{pct}%"],
                timeout=2, check=False,
            )
        except Exception as e:
            logger.warning(f"Erro ao ajustar volume do stream {idx}: {e}")
