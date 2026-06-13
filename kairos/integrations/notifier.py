"""Notificações de desktop — delega para kairos.platform.notifications.

Camada de integração pura. Mantida como ponto de entrada estável; a seleção
de implementação por SO vive em `kairos.platform.notifications`.
"""
from kairos.platform.notifications import notify  # noqa: F401 — re-export
