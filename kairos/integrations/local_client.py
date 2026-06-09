import json
import logging
import urllib.error
import urllib.request

from kairos.config import config as cfg

logger = logging.getLogger(__name__)

# Geração de notas pode demorar em CPU; timeout generoso.
_REQUEST_TIMEOUT_S = 300


class LocalError(Exception):
    """Erro do backend local (Ollama) — sempre com mensagem em PT-BR."""
    pass


def process(text: str, prompt: str) -> tuple[str, str]:
    """Processa texto via Ollama local (HTTP).

    Returns:
        Tupla (resultado, "ollama") em caso de sucesso.

    Raises:
        LocalError: serviço indisponível, modelo ausente ou resposta inválida.
    """
    config = cfg.load()
    host = str(config.get("ollama_host", "http://localhost:11434")).rstrip("/")
    model = config.get("ollama_model", "llama3.1:8b")

    payload = json.dumps({
        "model": model,
        "prompt": f"{prompt}\n\n{text}",
        "stream": False,
    }).encode("utf-8")

    request = urllib.request.Request(
        f"{host}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        logger.info("Processando via Ollama (modelo %s)...", model)
        with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise LocalError(
                f"Modelo '{model}' não encontrado no Ollama. "
                f"Baixe-o com: ollama pull {model}"
            ) from e
        raise LocalError(f"Falha na requisição ao Ollama: HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise LocalError(
            f"Ollama indisponível em {host} — inicie o serviço com 'ollama serve'. ({e.reason})"
        ) from e
    except Exception as e:  # noqa: BLE001 — converte qualquer falha em mensagem PT-BR
        raise LocalError(f"Erro inesperado ao processar no Ollama: {e}") from e

    answer = (data.get("response") or "").strip()
    if not answer:
        raise LocalError("O Ollama retornou uma resposta vazia.")

    logger.info("Resposta recebida do Ollama")
    return (answer, "ollama")
