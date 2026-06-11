import logging
import re
from datetime import datetime
from pathlib import Path

from kairos.config import config as cfg

logger = logging.getLogger(__name__)

_H1_RE = re.compile(r"^#\s+(.+?)\s*$")
_H2_RE = re.compile(r"^##\s+(.+?)\s*$")


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


def _note_name(name: str) -> str:
    """Nome de nota legível: remove só caracteres ilegais e colapsa espaços.

    Mantém os espaços para que os wikilinks [[Tema]] resolvam naturalmente no
    Obsidian (diferente de _filename_safe, que hifeniza para a nota única).
    """
    result = re.sub(r'[\\/:*?"<>|]', "", name)
    result = re.sub(r"\s+", " ", result).strip()
    return result or "nota"


def _split_sections(result: str) -> tuple[str | None, str, list[tuple[str, str]]]:
    """Divide o markdown em (título do tema, intro, [(sub-tema, corpo), ...]).

    Título do tema = primeiro heading `#`. Conteúdo antes do 1º `##` = intro.
    Cada `## X` (até o próximo `##`) vira um sub-tema. `###`+ ficam no corpo.
    """
    theme_title: str | None = None
    intro_lines: list[str] = []
    sections: list[tuple[str, str]] = []
    current_title: str | None = None
    current_body: list[str] = []
    seen_h2 = False

    for line in result.splitlines():
        h2 = _H2_RE.match(line)
        if h2:
            if current_title is not None:
                sections.append((current_title, "\n".join(current_body).strip()))
            current_title = h2.group(1).strip()
            current_body = []
            seen_h2 = True
            continue
        h1 = _H1_RE.match(line)
        if h1 and theme_title is None and not seen_h2:
            theme_title = h1.group(1).strip()
            continue
        if current_title is None:
            intro_lines.append(line)
        else:
            current_body.append(line)

    if current_title is not None:
        sections.append((current_title, "\n".join(current_body).strip()))

    return theme_title, "\n".join(intro_lines).strip(), sections


def _dedup_name(name: str, used: set[str]) -> str:
    """Garante nome único dentro da pasta do tema (case-insensitive)."""
    candidate = name
    n = 2
    while candidate.lower() in used:
        candidate = f"{name} {n}"
        n += 1
    used.add(candidate.lower())
    return candidate


def _write_theme(
    sections: list[tuple[str, str]],
    theme_name: str,
    intro: str,
    notes_dir: Path,
    front_matter: str,
    session_block: str,
    footer: str,
) -> str:
    """Cria <notes_dir>/<Tema>/ com a nota central + uma sub-nota por sub-tema.

    Reprocessar o mesmo tema reescreve a pasta (1 tema = 1 pasta). Retorna o
    caminho da nota central.
    """
    used: set[str] = {theme_name.lower()}
    theme_dir = notes_dir / theme_name
    try:
        theme_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Não foi possível criar a pasta do tema: {e}") from e

    sub_entries: list[tuple[str, str]] = []  # (nome final, corpo)
    for sub_title, body in sections:
        name = _dedup_name(_note_name(sub_title), used)
        sub_entries.append((name, body))

    # Reprocesso: remove sub-notas órfãs de uma execução anterior (sub-temas que
    # já não existem). Só apaga .md gerados pelo Kairos (frontmatter com tag
    # 'kairos') que não estão no novo conjunto — nunca toca notas do usuário.
    keep = {name for name, _ in sub_entries} | {theme_name}
    for f in theme_dir.glob("*.md"):
        if f.stem in keep:
            continue
        try:
            head = f.read_text(encoding="utf-8")[:400]
        except OSError:
            continue
        if "tags:" in head and "kairos" in head:
            try:
                f.unlink()
            except OSError as e:
                logger.warning("Não foi possível remover sub-nota órfã %s: %s", f, e)

    links = "\n".join(f"- [[{name}]]" for name, _ in sub_entries)
    intro_block = f"{intro}\n\n" if intro else ""
    central = (
        f"{front_matter}\n\n"
        f"# {theme_name}\n\n"
        f"{intro_block}"
        f"## Sub-temas\n\n{links}\n\n---\n\n{session_block}\n\n---\n\n{footer}\n"
    )

    central_path = theme_dir / f"{theme_name}.md"
    try:
        central_path.write_text(central, encoding="utf-8")
        for name, body in sub_entries:
            sub_content = (
                f"---\ntags: [kairos, pendente-revisao]\nparent: \"{theme_name}\"\n---\n\n"
                f"# {name}\n\n{body}\n\n---\n\n[[{theme_name}]]\n"
            )
            (theme_dir / f"{name}.md").write_text(sub_content, encoding="utf-8")
    except OSError as e:
        raise RuntimeError(f"Erro ao escrever notas do tema: {e}") from e

    logger.info("Tema salvo: %s (%d sub-notas)", central_path, len(sub_entries))
    return str(central_path)


def write(
    result: str,
    source_path: str,
    prompt_label: str,
    mode: str,
    session_objective: str = "",
    session_duration: str = "",
) -> str:
    """Gera e salva nota(s) Obsidian com o resultado do processamento.

    Quando o resultado processado tem sub-temas (headings `##`), cria uma pasta
    <Tema>/ com a nota central + uma sub-nota linkada por sub-tema. Caso
    contrário (sem `##` ou modo "fallback" com texto bruto), salva uma nota única
    — o comportamento original.

    Args:
        result: Texto processado (resposta do backend ou fallback bruto).
        source_path: Caminho completo do arquivo de origem.
        prompt_label: Label do prompt usado (ex: "Conceitos-chave").
        mode: backend usado ("notebooklm"/"gemini"/"ollama") ou "fallback".
        session_objective: Objetivo da sessão digitado pelo usuário.
        session_duration: Duração da sessão formatada (ex: "2m14s").

    Returns:
        Caminho completo do arquivo .md salvo (a nota central, no modo tema).

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

    processed_by = "local (bruto)" if mode == "fallback" else mode

    tags = ["kairos", "pendente-revisao"]
    if mode == "fallback":
        # Genérica: o fallback vale para qualquer backend (NotebookLM/Gemini/Ollama).
        tags.append("pendente-ia")
    tags_str = "[" + ", ".join(tags) + "]"

    objective_line = f"> Objetivo: {session_objective}" if session_objective else "> Objetivo: —"
    duration_str = session_duration if session_duration else "—"
    session_block = f"## Contexto da sessão\n\n{objective_line}"

    # Escapa aspas para não quebrar o YAML do frontmatter.
    safe_prompt_label = prompt_label.replace('"', "'")

    front_matter = f"""---
date: {date_str}
time: {time_str}
source: {source_name}
source_type: {source_type}
prompt: "{safe_prompt_label}"
processed_by: {processed_by}
tags: {tags_str}
session_duration: {duration_str}
---"""

    footer = (
        f"*Gerado pelo Kairos em {date_str} às {time_str}*\n"
        f"*Fonte original: {source_path}*"
    )

    # Modo tema: só para resultado realmente processado por um backend de IA.
    if mode != "fallback":
        theme_title, intro, sections = _split_sections(result)
        if sections:
            if len(sections) < 5:
                logger.warning(
                    "Tema '%s' gerado com apenas %d sub-tema(s); esperado no mínimo 5.",
                    theme_title or source_stem, len(sections),
                )
            theme_name = _note_name(theme_title or source_stem)
            return _write_theme(
                sections, theme_name, intro, notes_dir,
                front_matter, session_block, footer,
            )

    # Fallback: nota única (comportamento original).
    filename = f"{date_str}-{_filename_safe(source_stem)}.md"
    note_path = notes_dir / filename

    local_warning = (
        "\n> ⚠ **#pendente-ia** — Conteúdo bruto, não processado por um backend de IA."
        " Reprocesse quando o backend estiver disponível.\n"
        if mode == "fallback"
        else ""
    )

    content = f"""{front_matter}

# {source_stem} — {prompt_label}

## Resposta
{local_warning}
{result}

---

{session_block}

---

{footer}
"""

    try:
        note_path.write_text(content, encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Erro ao escrever arquivo: {e}") from e

    logger.info(f"Nota salva: {note_path}")
    return str(note_path)
