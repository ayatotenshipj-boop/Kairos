import logging
import re
from datetime import datetime
from pathlib import Path

from kairos.config import config as cfg

logger = logging.getLogger(__name__)


def _parse_source(source_path: str) -> tuple[str, str, str]:
    """Retorna (name_for_yaml, stem_for_title_and_filename, source_type).

    Trata URLs do YouTube separadamente de caminhos de arquivo para evitar
    que Path() quebre a URL em partes sem sentido.
    """
    if source_path.startswith("http"):
        m = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', source_path)
        if not m:
            m = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', source_path)
        if m:
            return (source_path, m.group(1), "youtube")
        stem = re.sub(r'https?://', '', source_path)
        stem = re.sub(r'[^\w-]', '_', stem)[:60].strip('_') or "url"
        return (source_path, stem, "url")
    path = Path(source_path)
    return (path.name, path.stem, path.suffix.lstrip(".").lower() or "file")


def _filename_safe(stem: str) -> str:
    result = re.sub(r'[\\/:*?"<>|]', "", stem)
    result = result.replace(" ", "-")
    result = re.sub(r"-+", "-", result).strip("-")
    return result


def write(
    result: str,
    source_path: str,
    prompt_label: str,
    mode: str,
    session_objective: str = "",
    session_duration: str = "",
) -> str:
    """Gera e salva nota Obsidian com o resultado do processamento.

    Args:
        result: Texto processado (resposta do NotebookLM ou fallback).
        source_path: Caminho completo do arquivo de origem.
        prompt_label: Label do prompt usado (ex: "Conceitos-chave").
        mode: "notebooklm" ou "local".
        session_objective: Objetivo da sessão digitado pelo usuário.
        session_duration: Duração da sessão formatada (ex: "2m14s").

    Returns:
        Caminho completo do arquivo .md salvo.

    Raises:
        ValueError: Se obsidian_vault_path não estiver configurado.
        RuntimeError: Se a escrita do arquivo falhar.
    """
    config = cfg.load()

    vault_path_str = config.get("obsidian_vault_path", "")
    if not vault_path_str or not vault_path_str.strip():
        raise ValueError("obsidian_vault_path não configurado")

    vault_path = Path(vault_path_str).expanduser()
    kairos_folder = config.get("kairos_folder", "kairos")
    notes_dir = vault_path / kairos_folder

    try:
        notes_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Não foi possível criar a pasta de notas: {e}") from e

    logger.info(f"Pasta de notas: {notes_dir}")

    source_name, source_stem, source_type = _parse_source(source_path)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    filename = f"{date_str}-{_filename_safe(source_stem)}.md"
    note_path = notes_dir / filename

    processed_by = "notebooklm" if mode == "notebooklm" else "local"

    tags = ["kairos", "pendente-revisao"]
    if mode == "local":
        tags.append("pendente-notebooklm")
    tags_str = "[" + ", ".join(tags) + "]"

    objective_line = f"> Objetivo: {session_objective}" if session_objective else "> Objetivo: —"
    duration_str = session_duration if session_duration else "—"

    local_warning = (
        "\n> ⚠ **#pendente-notebooklm** — Conteúdo bruto, não processado pelo NotebookLM."
        " Reprocesse quando o serviço estiver disponível.\n"
        if mode == "local"
        else ""
    )

    content = f"""---
date: {date_str}
time: {time_str}
source: {source_name}
source_type: {source_type}
prompt: "{prompt_label}"
processed_by: {processed_by}
tags: {tags_str}
session_duration: {duration_str}
---

# {source_stem} — {prompt_label}

## Resposta
{local_warning}
{result}

---

## Contexto da sessão

{objective_line}

---

*Gerado pelo Kairos em {date_str} às {time_str}*
*Fonte original: {source_path}*
"""

    try:
        note_path.write_text(content, encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Erro ao escrever arquivo: {e}") from e

    logger.info(f"Nota salva: {note_path}")
    return str(note_path)
