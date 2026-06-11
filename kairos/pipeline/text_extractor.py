import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Formatos de texto aceitos na DropZone e no ingestor (já são markdown/plain).
TEXT_SUFFIXES = ('.txt', '.md', '.markdown')


def extract_text(text_path: str) -> str:
    """Lê um arquivo de texto/markdown local.

    O conteúdo já é markdown/plain — sem conversão. O cap de tamanho fica a cargo
    do `processor` (choke point único), igual aos demais extractors.

    Args:
        text_path: Caminho completo para o arquivo .txt/.md/.markdown.

    Returns:
        Conteúdo do arquivo.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se a extensão não for suportada ou o arquivo estiver vazio.
        RuntimeError: Se a leitura falhar (mensagem PT-BR).
    """
    path = Path(text_path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {text_path}")

    if path.suffix.lower() not in TEXT_SUFFIXES:
        raise ValueError(f"Arquivo não é texto suportado: {path.name}")

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback para arquivos legados não-UTF-8.
        try:
            text = path.read_text(encoding="latin-1")
        except OSError as e:
            logger.error(f"Falha ao ler {text_path}: {e}")
            raise RuntimeError(f"Erro ao ler o arquivo de texto: {e}") from e
    except OSError as e:
        logger.error(f"Falha ao ler {text_path}: {e}")
        raise RuntimeError(f"Erro ao ler o arquivo de texto: {e}") from e

    if not text or not text.strip():
        raise ValueError("Arquivo de texto vazio")

    logger.info(f"Texto lido de {path.name}: {len(text)} caracteres")
    return text
