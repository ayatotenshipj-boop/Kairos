"""Verificação de atualização via API pública de releases do GitHub.

Best-effort e portável (urllib puro, como gemini_client/local_client): nunca
levanta exceção — em qualquer falha retorna "sem atualização". Compara a versão
empacotada (`kairos.__version__`) com a tag do último release.
"""

import json
import logging
import urllib.error
import urllib.request

from kairos._version import __version__

logger = logging.getLogger(__name__)

# Repositório oficial do Kairos. Constante de app (não é caminho de filesystem).
_RELEASES_API = "https://api.github.com/repos/ayatotenshipj-boop/Kairos/releases/latest"
_TIMEOUT_S = 8


def _parse_version(tag: str) -> tuple[int, ...]:
    """'v0.2.1' / '0.2.1' → (0, 2, 1). Ignora sufixos não numéricos por campo."""
    cleaned = tag.strip().lstrip("vV")
    parts: list[int] = []
    for chunk in cleaned.split("."):
        num = ""
        for ch in chunk:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    return tuple(parts)


def check_for_update(timeout: float = _TIMEOUT_S) -> dict:
    """Consulta o último release. Nunca levanta.

    Retorna dict:
      {"available": bool, "version": str, "url": str, "current": str}
    `available` é True só quando a versão remota é estritamente maior que a local.
    Em qualquer erro (rede, parsing, sem releases) → available=False.
    """
    result = {"available": False, "version": "", "url": "", "current": __version__}
    try:
        req = urllib.request.Request(
            _RELEASES_API,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Kairos-update-checker",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
        logger.info(f"Verificação de atualização indisponível: {e}")
        return result
    except Exception:
        logger.exception("Erro inesperado na verificação de atualização")
        return result

    tag = str(data.get("tag_name", "")).strip()
    if not tag:
        return result

    try:
        # Normaliza para 3 campos: evita que tag curta ('0.2') seja mal-ordenada
        # contra a local de 3 campos ('0.1.0') na comparação de tupla.
        def _norm3(t: tuple[int, ...]) -> tuple[int, int, int]:
            return (t + (0, 0, 0))[:3]
        is_newer = _norm3(_parse_version(tag)) > _norm3(_parse_version(__version__))
    except Exception:
        logger.exception("Erro ao comparar versões de atualização")
        return result

    if is_newer:
        # O html_url vem da resposta da API e termina aberto via
        # QDesktopServices.openUrl no SO. Só aceita http(s); senão cai para a
        # constante segura — bloqueia schemes perigosos (file:, smb:, ms-msdt:).
        raw_url = str(data.get("html_url", ""))
        safe_url = raw_url if raw_url.startswith(("https://", "http://")) else _RELEASES_API
        result["available"] = True
        result["version"] = tag.lstrip("vV")
        result["url"] = safe_url
    return result
