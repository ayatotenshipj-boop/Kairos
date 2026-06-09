import asyncio
import logging
import multiprocessing
import shutil
import subprocess
import sys
import time
from pathlib import Path
from queue import Empty

from notebooklm import NotebookLMClient
from notebooklm.exceptions import AuthError, ChatError, SourceAddError

from kairos.config import config as cfg

logger = logging.getLogger(__name__)

# Tempo máximo total do processamento (extração já ocorreu antes desta etapa).
_PROCESS_TIMEOUT_S = 300

# Tempo máximo da verificação de sessão (local é rápido; com rede pode demorar).
_AUTH_CHECK_TIMEOUT_S = 30


class NotebookLMError(Exception):
    """Erro do cliente NotebookLM — sempre com mensagem em PT-BR."""
    pass


def _notebooklm_cli() -> str | None:
    """Localiza o executável da CLI `notebooklm`.

    `shutil.which` só acha quando o venv está no PATH (ex.: via run.sh). Como
    fallback, procura ao lado do interpretador atual (`.venv/bin/notebooklm`).
    """
    exe = shutil.which("notebooklm")
    if exe:
        return exe
    sibling = Path(sys.executable).parent / "notebooklm"
    if sibling.exists():
        return str(sibling)
    return None


def auth_check(test_network: bool = False) -> tuple[bool, str]:
    """Verifica a sessão do NotebookLM via CLI `notebooklm auth check`.

    Args:
        test_network: se True, acrescenta `--test` (faz requisição à rede).
            Por padrão só valida localmente (storage + cookies) — rápido.

    Returns:
        (ok, mensagem_ptbr). Em caso de falha, a mensagem segue o padrão
        "o quê + por quê + o que fazer". NUNCA lança.
    """
    exe = _notebooklm_cli()
    if exe is None:
        # Sem CLI não dá para verificar; não alarmar falsamente nem bloquear.
        logger.info("CLI 'notebooklm' não encontrada — pulando verificação de sessão.")
        return (True, "")

    cmd = [exe, "auth", "check", "--json"]
    if test_network:
        cmd.append("--test")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_AUTH_CHECK_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return (False, "Tempo limite ao verificar a sessão do NotebookLM.")
    except Exception as e:  # noqa: BLE001 — converte qualquer falha em PT-BR
        logger.warning("Falha ao executar verificação de sessão: %s", e)
        return (False, f"Não foi possível verificar a sessão do NotebookLM: {e}")

    if proc.returncode == 0:
        return (True, "")

    logger.info("auth check retornou código %s: %s", proc.returncode, proc.stderr.strip())
    return (
        False,
        "Sessão do NotebookLM expirada — rode no terminal: notebooklm auth refresh",
    )


def _subprocess_entry(text: str, prompt: str, result_queue) -> None:
    """Executa o processamento NotebookLM e devolve o resultado pela fila.

    Roda num processo SEPARADO (spawn): a automação de browser do Playwright
    nunca compartilha o processo da UI Qt — um crash nativo aqui não derruba o app.
    Traduz toda exceção para mensagem PT-BR antes de enfileirar.
    """
    try:
        answer = asyncio.run(_process_async(text, prompt))
        result_queue.put(("ok", answer))
    except NotebookLMError as e:
        result_queue.put(("err", str(e)))
    except AuthError:
        result_queue.put((
            "err",
            "Sessão do NotebookLM expirou. Execute 'notebooklm login' no terminal.",
        ))
    except SourceAddError:
        result_queue.put(("err", "Falha ao enviar conteúdo para o NotebookLM."))
    except ChatError:
        result_queue.put(("err", "Falha ao processar o prompt no NotebookLM."))
    except Exception as e:  # noqa: BLE001 — converte qualquer falha em mensagem PT-BR
        result_queue.put(("err", f"Erro inesperado no NotebookLM: {e}"))


def process(text: str, prompt: str) -> tuple[str, str]:
    """Processa texto via NotebookLM num subprocesso isolado.

    O NotebookLM usa Playwright/Chromium; rodá-lo dentro de um QThread da UI Qt
    pode causar crash nativo. Isolando em processo separado, qualquer crash vira
    NotebookLMError e o pipeline cai no fallback local sem derrubar a interface.

    Returns:
        Tupla (resposta, "notebooklm") em caso de sucesso.

    Raises:
        NotebookLMError: Falha de autenticação, API, timeout, crash ou inesperada.
    """
    ctx = multiprocessing.get_context("spawn")
    result_queue = ctx.Queue()
    proc = ctx.Process(target=_subprocess_entry, args=(text, prompt, result_queue))
    proc.start()

    result = None
    deadline = time.monotonic() + _PROCESS_TIMEOUT_S
    while time.monotonic() < deadline:
        try:
            result = result_queue.get(timeout=1.0)
            break
        except Empty:
            if not proc.is_alive():
                break  # processo terminou sem enfileirar resultado (crash nativo)

    if proc.is_alive():
        proc.terminate()
        proc.join(5)
        raise NotebookLMError("Tempo limite ao processar no NotebookLM.")

    proc.join(5)

    if result is None:
        logger.error(f"Subprocesso NotebookLM encerrou sem resultado (exitcode={proc.exitcode})")
        raise NotebookLMError("O processamento do NotebookLM encerrou inesperadamente.")

    status, payload = result
    if status == "ok":
        return (payload, "notebooklm")
    raise NotebookLMError(payload)


async def _process_async(text: str, prompt: str) -> str:
    """Implementação assíncrona do processamento."""
    config = cfg.load()
    notebooklm_home = Path(config.get("notebooklm_home", "~/.notebooklm")).expanduser()

    # NotebookLMClient.from_storage espera caminho para storage_state.json, não diretório
    if notebooklm_home.is_dir():
        # Usa estrutura padrão: ~/.notebooklm/profiles/default/storage_state.json
        storage_path = notebooklm_home / "profiles" / "default" / "storage_state.json"
    else:
        # Se for arquivo, usa diretamente
        storage_path = notebooklm_home

    # Valida que o arquivo existe
    if not storage_path.exists():
        raise NotebookLMError(
            f"Arquivo de autenticação não encontrado: {storage_path}. "
            "Execute 'notebooklm login' no terminal para autenticar."
        )

    if storage_path.is_dir():
        raise NotebookLMError(
            f"Caminho de autenticação é um diretório, esperava arquivo: {storage_path}"
        )

    logger.info("Conectando ao NotebookLM...")
    async with NotebookLMClient.from_storage(path=str(storage_path)) as client:
        logger.info("Criando notebook temporário...")
        notebook = await asyncio.wait_for(
            client.notebooks.create(title="Kairos — processamento temporário"),
            timeout=30.0,
        )

        try:
            logger.info(f"Subindo conteúdo ({len(text)} caracteres)...")
            await asyncio.wait_for(
                client.sources.add_text(
                    notebook_id=notebook.id,
                    title="Conteúdo extraído",
                    content=text,
                    wait=True,
                ),
                timeout=120.0,
            )

            logger.info("Processando com o prompt...")
            result = await asyncio.wait_for(
                client.chat.ask(
                    notebook_id=notebook.id,
                    question=prompt,
                ),
                timeout=120.0,
            )

            logger.info("Resposta recebida do NotebookLM")
            return result.answer

        finally:
            logger.info("Limpando notebook temporário...")
            try:
                await asyncio.wait_for(client.notebooks.delete(notebook.id), timeout=10.0)
            except Exception as cleanup_error:
                logger.warning(f"Falha ao deletar notebook: {cleanup_error}")
