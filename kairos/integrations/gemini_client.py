import logging
import os

from google import genai
from google.genai import errors as genai_errors

from kairos.config import config as cfg

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Erro do backend Gemini — sempre com mensagem em PT-BR."""
    pass


def process(text: str, prompt: str) -> tuple[str, str]:
    """Processa texto via Gemini (google-genai).

    Returns:
        Tupla (resultado, "gemini") em caso de sucesso.

    Raises:
        GeminiError: chave ausente, falha de rede/API ou resposta vazia.
    """
    config = cfg.load()
    api_key = (config.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise GeminiError(
            "Chave da API do Gemini não configurada. "
            "Defina-a nas Configurações ou na variável de ambiente GEMINI_API_KEY."
        )

    model = config.get("gemini_model", "gemini-flash-latest")

    try:
        logger.info("Processando via Gemini (modelo %s)...", model)
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=f"{prompt}\n\n{text}",
        )
    except genai_errors.APIError as e:
        raise GeminiError(f"Falha na API do Gemini: {e}") from e
    except Exception as e:  # noqa: BLE001 — converte qualquer falha em mensagem PT-BR
        raise GeminiError(f"Erro inesperado ao processar no Gemini: {e}") from e

    answer = (response.text or "").strip()
    if not answer:
        raise GeminiError("O Gemini retornou uma resposta vazia.")

    logger.info("Resposta recebida do Gemini")
    return (answer, "gemini")
