import logging
from pathlib import Path

import pymupdf4llm

logger = logging.getLogger(__name__)


def extract_text(pdf_path: str) -> str:
    """Extrai texto de um PDF usando pymupdf4llm.

    Args:
        pdf_path: Caminho completo para o arquivo PDF.

    Returns:
        Texto extraído em formato markdown.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se o arquivo não for um PDF válido ou estiver vazio.
        RuntimeError: Se a extração falhar por outro motivo.
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Arquivo não é um PDF: {pdf_path}")

    try:
        text = pymupdf4llm.to_markdown(pdf_path)
    except Exception as e:
        logger.error(f"Falha ao extrair texto de {pdf_path}: {e}")
        raise RuntimeError(f"Erro ao processar o PDF: {e}") from e

    if not text or not text.strip():
        raise ValueError("PDF vazio ou sem texto extraível")

    logger.info(f"Texto extraído de {path.name}: {len(text)} caracteres")
    return text
