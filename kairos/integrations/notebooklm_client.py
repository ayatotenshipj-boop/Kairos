import asyncio
import logging
from pathlib import Path

from notebooklm import NotebookLMClient
from notebooklm.exceptions import AuthError, SourceAddError, ChatError

from kairos.config import config as cfg

logger = logging.getLogger(__name__)


class NotebookLMError(Exception):
    """Erro do cliente NotebookLM — sempre com mensagem em PT-BR."""
    pass


def process(text: str, prompt: str) -> str:
    """Processa texto via NotebookLM: cria notebook, sobe texto, aplica prompt.

    Returns:
        Resposta do NotebookLM como string.

    Raises:
        NotebookLMError: Qualquer falha de autenticação, API ou inesperada.
    """
    try:
        return asyncio.run(_process_async(text, prompt))
    except AuthError as e:
        logger.error(f"Autenticação NotebookLM falhou: {e}")
        raise NotebookLMError(
            "Sessão do NotebookLM expirou. Execute 'notebooklm login' no terminal."
        ) from e
    except SourceAddError as e:
        logger.error(f"Falha ao enviar conteúdo: {e}")
        raise NotebookLMError("Falha ao enviar conteúdo para o NotebookLM.") from e
    except ChatError as e:
        logger.error(f"Falha no processamento do prompt: {e}")
        raise NotebookLMError("Falha ao processar o prompt no NotebookLM.") from e
    except Exception as e:
        logger.exception("Erro inesperado ao processar via NotebookLM")
        raise NotebookLMError(f"Erro inesperado no NotebookLM: {e}") from e


async def _process_async(text: str, prompt: str) -> str:
    """Implementação assíncrona do processamento."""
    config = cfg.load()
    storage_path = str(Path(config.get("notebooklm_home", "~/.notebooklm")).expanduser())

    logger.info("Conectando ao NotebookLM...")
    async with NotebookLMClient.from_storage(path=storage_path) as client:
        logger.info("Criando notebook temporário...")
        notebook = await client.notebooks.create(title="Kairos — processamento temporário")

        try:
            logger.info(f"Subindo conteúdo ({len(text)} caracteres)...")
            await client.sources.add_text(
                notebook_id=notebook.id,
                title="Conteúdo extraído",
                content=text,
            )

            logger.info("Processando com o prompt...")
            result = await client.chat.ask(
                notebook_id=notebook.id,
                question=prompt,
            )

            logger.info("Resposta recebida do NotebookLM")
            return result.answer

        finally:
            logger.info("Limpando notebook temporário...")
            try:
                await client.notebooks.delete(notebook.id)
            except Exception as cleanup_error:
                logger.warning(f"Falha ao deletar notebook: {cleanup_error}")
