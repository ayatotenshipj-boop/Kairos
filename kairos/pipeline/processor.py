import logging

from kairos.config import config as cfg
from kairos.config.defaults import STRUCTURE_INSTRUCTION

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


class ProcessorError(Exception):
    """Falha no processamento que exige decisão do usuário (não cai em silêncio
    para local). `category` ∈ {"too_large", "unavailable", "backend"} orienta a
    mensagem PT-BR exibida no diálogo de escolha.
    """

    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category
        self.message = message


def build_fallback(text: str) -> str:
    """Texto bruto + rodapé de fallback — usado ao salvar localmente (#pendente)."""
    return text + _FALLBACK_FOOTER


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
    """Roteia o texto para o backend configurado.

    Em falha NÃO cai em silêncio para local: levanta ProcessorError para que a UI
    ofereça ao usuário a escolha (salvar localmente / cancelar).

    Returns:
        Tupla (resultado, modo) — modo "notebooklm" / "gemini" / "ollama".

    Raises:
        ProcessorError: arquivo muito grande, backend indisponível ou falha.
    """
    backend = cfg.load().get("processor_backend", "notebooklm")
    if backend not in _VALID_BACKENDS:
        logger.warning("Backend desconhecido '%s', usando notebooklm", backend)
        backend = "notebooklm"

    # Arquivo muito grande → decisão do usuário (em vez de truncar silenciosamente).
    max_chars = cfg.load().get("processor_max_chars", 30000)
    if len(text) > max_chars:
        raise ProcessorError(
            "too_large",
            f"O conteúdo tem {len(text):,} caracteres e excede o limite de "
            f"{max_chars:,} do backend de IA. Processá-lo pode falhar ou perder "
            f"informação.".replace(",", "."),
        )

    try:
        fn, backend_error = _resolve_backend(backend)
    except Exception as e:
        # Dependência do backend ausente/quebrada (ex.: SDK não instalado).
        logger.exception("Falha ao carregar o backend '%s'.", backend)
        raise ProcessorError(
            "backend",
            f"Não foi possível carregar o backend '{backend}': {e}",
        ) from e

    # Injeção arquitetural: todo prompt recebe a instrução fixa de estrutura
    # (tema + sub-temas) antes de ir ao backend. Não editável pelo usuário.
    final_prompt = prompt_text + "\n\n" + STRUCTURE_INSTRUCTION
    logger.debug("Prompt final montado:\n%s", final_prompt)

    try:
        logger.info("Processando via backend '%s'...", backend)
        result, mode = fn(text, final_prompt)
        logger.info("Processamento via '%s' bem-sucedido", backend)
        return (result, mode)

    except backend_error as e:
        logger.warning("Backend '%s' indisponível: %s", backend, e)
        raise ProcessorError("unavailable", str(e)) from e

    except Exception as e:
        logger.exception("Erro inesperado durante o processamento.")
        raise ProcessorError(
            "backend", f"Erro inesperado no processamento: {e}"
        ) from e
