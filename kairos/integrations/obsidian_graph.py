import logging
import re
from pathlib import Path

from kairos.config import config as cfg

logger = logging.getLogger(__name__)

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:\|[^\]]+)?\]\]")


def _extract_wikilinks(text: str) -> list[str]:
    """Retorna os alvos de [[wikilink]] na ordem em que aparecem, sem repetir."""
    seen: set[str] = set()
    result: list[str] = []
    for m in _WIKILINK_RE.finditer(text):
        target = m.group(1).strip()
        if target and target not in seen:
            seen.add(target)
            result.append(target)
    return result


def read_theme(note_path: str) -> dict:
    """Lê a pasta do tema e devolve a estrutura do grafo para o mapa.

    Read-only: o Kairos desenha o que já está no vault, não gera. Lê apenas a
    pasta do tema recém-processado — nunca escaneia o vault inteiro.

    Args:
        note_path: caminho da nota central retornado pelo writer.

    Returns:
        {"central": str, "central_path": str, "nodes": [{"label": str, "path": str}]}
        ou {} quando o caminho é uma nota única (fora de uma pasta de tema).
    """
    p = Path(note_path)
    folder = p.parent

    kairos_folder = cfg.load().get("kairos_folder", "kairos")

    # Guarda anti-falso-positivo: a nota só é uma central de tema se mora numa
    # pasta homônima, diretamente sob a pasta do Kairos. A nota única mora direto
    # em <vault>/<kairos_folder>/, cujo parent.name == kairos_folder != stem.
    is_theme = folder.name == p.stem and folder.parent.name == kairos_folder
    if not is_theme:
        return {}

    try:
        central_text = p.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("Não foi possível ler a nota central %s: %s", p, e)
        return {}

    # Mapa nome-da-nota -> caminho, para as notas .md da pasta (exceto a central).
    siblings = {
        f.stem: f
        for f in folder.glob("*.md")
        if f.name != p.name
    }

    # Ordem dos nós segue os [[wikilinks]] da central; fallback para a listagem.
    nodes: list[dict] = []
    used: set[str] = set()
    for label in _extract_wikilinks(central_text):
        f = siblings.get(label)
        if f is not None and label not in used:
            nodes.append({"label": label, "path": str(f)})
            used.add(label)
    for stem, f in siblings.items():
        if stem not in used:
            nodes.append({"label": stem, "path": str(f)})
            used.add(stem)

    return {
        "central": p.stem,
        "central_path": str(p),
        "nodes": nodes,
    }
