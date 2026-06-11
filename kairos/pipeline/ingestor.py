import logging
from pathlib import Path

from kairos.pipeline import (
    audio_extractor,
    pdf_extractor,
    text_extractor,
    youtube_extractor,
)

logger = logging.getLogger(__name__)


def _is_youtube_url(source: str) -> bool:
    return 'youtube.com' in source or 'youtu.be' in source


def ingest(source: str) -> tuple[str, str]:
    """Recebe path de PDF/áudio ou URL do YouTube e retorna (texto_extraído, tipo).

    Args:
        source: Caminho completo de um arquivo PDF/áudio ou URL do YouTube.

    Returns:
        Tupla (texto, tipo) onde tipo é "pdf", "text", "audio" ou "youtube".

    Raises:
        ValueError: Tipo de fonte não suportado.
        FileNotFoundError: Arquivo PDF não encontrado.
        RuntimeError: Falha na extração com mensagem PT-BR.
    """
    if _is_youtube_url(source):
        logger.info(f"Fonte identificada como YouTube: {source}")
        text = youtube_extractor.extract(source)
        return (text, 'youtube')

    path = Path(source)
    if path.suffix.lower() == '.pdf':
        logger.info(f"Fonte identificada como PDF: {path.name}")
        text = pdf_extractor.extract_text(source)
        return (text, 'pdf')

    if path.suffix.lower() in text_extractor.TEXT_SUFFIXES:
        logger.info(f"Fonte identificada como texto: {path.name}")
        text = text_extractor.extract_text(source)
        return (text, 'text')

    if path.suffix.lower() in audio_extractor.AUDIO_SUFFIXES:
        logger.info(f"Fonte identificada como áudio: {path.name}")
        text = audio_extractor.extract_text(source)
        return (text, 'audio')

    raise ValueError(f"Tipo de fonte não suportado: {path.name or source}")
