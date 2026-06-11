import logging
from pathlib import Path

from kairos.pipeline.youtube_extractor import _normalize_transcript, _transcribe_whisper

logger = logging.getLogger(__name__)

# Formatos aceitos na DropZone e no ingestor (decodificados pelo faster-whisper/av).
AUDIO_SUFFIXES = ('.mp3', '.wav', '.m4a', '.ogg', '.opus', '.flac')


def extract_text(audio_path: str) -> str:
    """Transcreve um arquivo de áudio local com faster-whisper.

    Args:
        audio_path: Caminho completo para o arquivo de áudio.

    Returns:
        Texto transcrito.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se a extensão não for um áudio suportado.
        RuntimeError: Se a transcrição falhar (mensagem PT-BR).
    """
    path = Path(audio_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {audio_path}")

    if path.suffix.lower() not in AUDIO_SUFFIXES:
        raise ValueError(f"Arquivo não é um áudio suportado: {path.name}")

    try:
        text = _transcribe_whisper(path)
    except RuntimeError:
        raise
    except Exception as e:
        logger.error(f"Falha ao transcrever {audio_path}: {e}")
        raise RuntimeError(f"Erro ao transcrever o áudio: {e}") from e

    text = _normalize_transcript(text)
    logger.info(f"Áudio transcrito de {path.name}: {len(text)} caracteres")
    return text
