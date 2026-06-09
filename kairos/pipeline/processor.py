import logging

from kairos.config import config as cfg

logger = logging.getLogger(__name__)

_FALLBACK_FOOTER = (
    "\n\n---\n\n"
    "**Nota:** Conteúdo bruto — backend de IA indisponível no momento do "
    "processamento. Verifique a conexão/sessão do backend escolhido e reprocesse "
    "quando possível."
)

# Backends disponíveis. Cada client expõe process(text, prompt) -> tuple[str, str]
# e lança um erro tipado em caso de falha. Imports lazy para não acoplar o
# import-time deste módulo às dependências de cada backend (SDK Gemini etc.).
_VALID_BACKENDS = ("notebooklm", "gemini", "ollama")


def _resolve_backend(name: str):
    """Retorna (função process, exceção tipada) do backend escolhido."""
    if name == "gemini":
        from kairos.integrations import gemini_client
        return gemini_client.process, gemini_client.GeminiError
    if name == "ollama":
        from kairos.integrations import local_client
        return local_client.process, local_client.LocalError
    from kairos.integrations import notebooklm_client
    return notebooklm_client.process, notebooklm_client.NotebookLMError


def process(text: str, prompt_text: str) -> tuple[str, str]:
    """Roteia o texto para o backend configurado ou retorna fallback local.

    Nunca lança exceção — sempre retorna (resultado, modo).

    Returns:
        Tupla (resultado, modo):
        - modo "notebooklm" / "gemini" / "ollama": resultado processado pelo backend
        - modo "fallback": texto bruto com nota de rodapé (backend indisponível)
    """
    backend = cfg.load().get("processor_backend", "notebooklm")
    if backend not in _VALID_BACKENDS:
        logger.warning("Backend desconhecido '%s', usando notebooklm", backend)
        backend = "notebooklm"

    try:
        fn, backend_error = _resolve_backend(backend)
    except Exception:
        # Dependência do backend ausente/quebrada (ex.: SDK não instalado).
        logger.exception(
            "Falha ao carregar o backend '%s'. Usando fallback local.", backend
        )
        return (text + _FALLBACK_FOOTER, "fallback")

    try:
        logger.info("Processando via backend '%s'...", backend)
        result, mode = fn(text, prompt_text)
        logger.info("Processamento via '%s' bem-sucedido", backend)
        return (result, mode)

    except backend_error as e:
        logger.warning("Backend '%s' indisponível, usando fallback local: %s", backend, e)
        return (text + _FALLBACK_FOOTER, "fallback")

    except Exception:
        # ATENÇÃO: Este bloco não deveria ser atingido em operação normal.
        # Se atingido, indica BUG no código (não falha do backend).
        # Stack trace completo é logado para debug.
        logger.exception(
            "ERRO CRÍTICO: Exceção inesperada durante processamento. "
            "Isto indica bug no código, não falha do backend. "
            "Usando fallback local para evitar perda de dados."
        )
        return (text + _FALLBACK_FOOTER, "fallback")
