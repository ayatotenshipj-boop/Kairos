import logging

from kairos.integrations import notebooklm_client
from kairos.integrations.notebooklm_client import NotebookLMError

logger = logging.getLogger(__name__)

_FALLBACK_FOOTER = (
    "\n\n---\n\n"
    "**Nota:** Conteúdo bruto — NotebookLM indisponível no momento do processamento. "
    "Execute `notebooklm login` no terminal e reprocesse quando possível."
)


def process(text: str, prompt_text: str) -> tuple[str, str]:
    """Processa texto via NotebookLM ou retorna fallback local.

    Nunca lança exceção — sempre retorna (resultado, modo).

    Returns:
        Tupla (resultado, modo):
        - modo "notebooklm": resultado é a resposta processada
        - modo "local": resultado é o texto bruto com nota de rodapé
    """
    try:
        logger.info("Tentando processar via NotebookLM...")
        result = notebooklm_client.process(text, prompt_text)
        logger.info("Processamento via NotebookLM bem-sucedido")
        return (result, "notebooklm")

    except NotebookLMError as e:
        logger.warning(f"NotebookLM indisponível, usando fallback local: {e}")
        return (text + _FALLBACK_FOOTER, "local")

    except Exception as e:
        # ATENÇÃO: Este bloco não deveria ser atingido em operação normal.
        # Se atingido, indica BUG no código (não falha do NotebookLM).
        # Stack trace completo é logado para debug.
        logger.exception(
            "ERRO CRÍTICO: Exceção inesperada durante processamento. "
            "Isto indica bug no código, não falha do NotebookLM. "
            "Usando fallback local para evitar perda de dados."
        )
        return (text + _FALLBACK_FOOTER, "local")
