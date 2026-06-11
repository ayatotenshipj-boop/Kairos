import json
import logging
import urllib.error
import urllib.request

from kairos.config import config as cfg

logger = logging.getLogger(__name__)

# Geração de notas pode demorar em CPU; timeout generoso.
_REQUEST_TIMEOUT_S = 300


class LocalError(Exception):
    """Erro do backend local — sempre com mensagem em PT-BR."""
    pass


def _first_model(host: str) -> str:
    """Pergunta ao servidor local quais modelos existem e retorna o primeiro.

    O Kairos não assume nenhum modelo: o servidor é a fonte da verdade.
    """
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise LocalError(
            f"Servidor local indisponível em {host} — inicie o serviço e tente de novo. ({e.reason})"
        ) from e
    except Exception as e:  # noqa: BLE001 — converte qualquer falha em mensagem PT-BR
        raise LocalError(f"Não foi possível consultar o servidor local em {host}: {e}") from e

    models = data.get("models") or []
    for m in models:
        name = (m.get("model") or m.get("name") or "").strip()
        if name:
            return name
    raise LocalError(
        "Nenhum modelo disponível no servidor local — carregue um modelo e tente de novo."
    )


def process(text: str, prompt: str) -> tuple[str, str]:
    """Processa texto via servidor local (HTTP), modelo inferido pelo servidor.

    Returns:
        Tupla (resultado, "ollama") em caso de sucesso.

    Raises:
        LocalError: serviço indisponível, sem modelo ou resposta inválida.
    """
    config = cfg.load()
    host = str(config.get("local_endpoint", "http://localhost:11434")).rstrip("/")
    model = _first_model(host)

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
        logger.info("Processando via servidor local (modelo %s)...", model)
        with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise LocalError(
                f"Modelo '{model}' não encontrado no servidor local. "
                f"Carregue-o e tente de novo."
            ) from e
        raise LocalError(f"Falha na requisição ao servidor local: HTTP {e.code}") from e
    except urllib.error.URLError as e:
        raise LocalError(
            f"Servidor local indisponível em {host} — inicie o serviço e tente de novo. ({e.reason})"
        ) from e
    except Exception as e:  # noqa: BLE001 — converte qualquer falha em mensagem PT-BR
        raise LocalError(f"Erro inesperado ao processar no servidor local: {e}") from e

    answer = (data.get("response") or "").strip()
    if not answer:
        raise LocalError("O servidor local retornou uma resposta vazia.")

    logger.info("Resposta recebida do servidor local")
    return (answer, "ollama")
