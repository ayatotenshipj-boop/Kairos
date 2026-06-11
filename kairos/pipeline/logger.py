import logging
from datetime import datetime
from pathlib import Path

from kairos.config import config as cfg
from kairos.util import format_duration

logger = logging.getLogger(__name__)

_HEADER = (
    "| Data | Hora | Fonte | Prompt | Status | Duração | Modo |\n"
    "|------|------|-------|--------|--------|---------|------|\n"
)


def log_session(
    source: str,
    prompt_label: str,
    status: str,
    duration_seconds: float,
    mode: str,
) -> None:
    """Registra uma sessão no study-log.md do vault Obsidian.

    Nunca lança exceção — erros são logados e a função retorna silenciosamente.
    """
    try:
        config = cfg.load()

        vault_path_str = config.get("obsidian_vault_path", "")
        if not vault_path_str or not vault_path_str.strip():
            logger.warning("log_session: vault não configurado, registro ignorado")
            return

        vault_path = Path(vault_path_str).expanduser()
        kairos_folder = config.get("kairos_folder", "kairos")
        log_filename = config.get("log_filename", "study-log.md")
        log_path = vault_path / kairos_folder / log_filename

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")

        if source and source.startswith("http"):
            source_name = source
        else:
            source_name = Path(source).name if source else source

        duration_str = format_duration(duration_seconds)

        row = (
            f"| {date_str} | {time_str} | {source_name} | "
            f"{prompt_label} | {status} | {duration_str} | {mode} |\n"
        )

        log_path.parent.mkdir(parents=True, exist_ok=True)

        if not log_path.exists():
            log_path.write_text(_HEADER + row, encoding="utf-8")
        else:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(row)

        logger.info(f"Sessão registrada em {log_path}")

    except Exception as e:
        logger.error(f"Erro ao registrar sessão no log: {e}")
