"""Discord Rich Presence via pypresence — best-effort, nunca trava o Kairos.

Camada de integração pura (sem UI, sem lógica de negócio). Toda chamada é
resiliente: Discord fechado, lib ausente ou App ID não configurado viram no-op
silencioso. As chamadas IPC rodam num thread daemon para não bloquear a GUI.

Requer um Application (Client) ID do Discord Developer Portal, salvo em
`discord_client_id`; sem ele, o recurso fica inativo mesmo com o toggle ligado.
"""

import logging
import threading
import time

from kairos.config import config as cfg

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_rpc = None
_connected = False
_start_ts: int | None = None


def _client_id() -> str:
    return str(cfg.load().get("discord_client_id", "") or "").strip()


def _enabled() -> bool:
    return bool(cfg.load().get("discord_presence", False)) and bool(_client_id())


def _ensure_connected() -> bool:
    """Conecta ao Discord se necessário. Chamado já sob _lock."""
    global _rpc, _connected, _start_ts
    if _connected and _rpc is not None:
        return True
    try:
        from pypresence import Presence
        _rpc = Presence(_client_id())
        _rpc.connect()
        _connected = True
        _start_ts = int(time.time())
        return True
    except Exception as e:
        # Discord fechado, lib ausente ou App ID inválido → segue sem presença.
        logger.info("Discord Rich Presence indisponível: %s", e)
        _rpc = None
        _connected = False
        return False


def _close_locked() -> None:
    global _rpc, _connected, _start_ts
    if _rpc is not None:
        try:
            _rpc.clear()
        except Exception:
            pass
        try:
            _rpc.close()
        except Exception:
            pass
    _rpc = None
    _connected = False
    _start_ts = None


def _apply(state: str, details: str) -> None:
    with _lock:
        if not _enabled():
            _close_locked()
            return
        if not _ensure_connected() or _rpc is None:
            return
        try:
            # large_image/small_image referenciam ASSET KEYS cadastrados no
            # Discord Developer Portal → Rich Presence → Art Assets (faça upload
            # de kairos/images/kairos_discord_rpc_large/small com estes nomes).
            _rpc.update(
                state=state or None,
                details=details or None,
                start=_start_ts,
                large_image="kairos_discord_rpc_large_1024x1024",
                large_text="Kairos",
                small_image="kairos_discord_rpc_small_512x512",
                small_text="o momento de aprender",
            )
        except Exception as e:
            logger.info("Falha ao atualizar Discord Rich Presence: %s", e)
            _close_locked()


def set_state(state: str, details: str = "") -> None:
    """Atualiza a presença em segundo plano (não bloqueia a GUI)."""
    threading.Thread(target=_apply, args=(state, details), daemon=True).start()


def shutdown() -> None:
    """Fecha a conexão (chamado no encerramento do app)."""
    with _lock:
        _close_locked()
