"""Notificações de desktop via `notify-send`.

Camada de integração pura — sem UI, sem lógica de negócio. Best-effort: nenhuma
função levanta exceção; falha vira no-op (ex.: `notify-send` ausente).
"""

import logging
import shutil
import subprocess

logger = logging.getLogger(__name__)

_APP_NAME = "Kairos"


def notify(title: str, body: str = "") -> None:
    """Envia uma notificação de desktop. No-op se `notify-send` não existir."""
    exe = shutil.which("notify-send")
    if not exe:
        logger.info("notify-send não encontrado — notificação de desktop indisponível")
        return
    try:
        subprocess.run(
            [exe, "-a", _APP_NAME, title, body],
            timeout=5,
            check=False,
        )
    except Exception as e:  # noqa: BLE001 — best-effort, nunca propaga
        logger.warning(f"Erro ao enviar notificação: {e}")
