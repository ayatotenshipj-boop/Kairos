import json
import logging
from pathlib import Path

from kairos.config.defaults import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path.home() / ".config" / "kairos" / "config.json"
_PROMPTS_PATH = Path.home() / ".config" / "kairos" / "prompts.json"
# Template versionado, empacotado junto do código (read-only). Semeia a cópia
# do usuário na 1ª execução.
_PROMPTS_TEMPLATE = Path(__file__).parent / "prompts.json"


def load() -> dict:
    if not _CONFIG_PATH.exists():
        logger.info("Config não encontrado, criando com padrões")
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        save(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Migração: campo legado "ollama_host" → "local_endpoint" (back-compat).
        if "local_endpoint" not in data and "ollama_host" in data:
            data["local_endpoint"] = data["ollama_host"]
        config = dict(DEFAULT_CONFIG)
        for key, value in data.items():
            default = DEFAULT_CONFIG.get(key)
            # Chave conhecida com tipo divergente do default → descarta (config
            # corrompido não deve derrubar a app). bool é subtipo de int, então
            # trata-se à parte para não aceitar int onde se espera bool.
            if key in DEFAULT_CONFIG:
                if isinstance(default, bool) and not isinstance(value, bool):
                    logger.warning("Config '%s' com tipo inválido, usando padrão", key)
                    continue
                if not isinstance(value, type(default)):
                    logger.warning("Config '%s' com tipo inválido, usando padrão", key)
                    continue
            config[key] = value
        return config
    except Exception as e:
        logger.error(f"Erro ao ler config em {_CONFIG_PATH}: {e}")
        return dict(DEFAULT_CONFIG)


def save(config: dict) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        logger.info(f"Config salvo em {_CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Erro ao salvar config: {e}")
        raise RuntimeError(f"Erro ao salvar configuração: {e}") from e


def prompts_path() -> Path:
    return _PROMPTS_PATH


def _read_template_prompts() -> list:
    try:
        with open(_PROMPTS_TEMPLATE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"Erro ao ler template de prompts em {_PROMPTS_TEMPLATE}: {e}")
        return []


def _legacy_prompts_from_config() -> list:
    """Lê prompts embutidos num config.json em formato antigo, se houver."""
    if not _CONFIG_PATH.exists():
        return []
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        legacy = data.get("prompts")
        return legacy if isinstance(legacy, list) and legacy else []
    except Exception:
        return []


def load_prompts() -> list:
    """Carrega os prompts do usuário (~/.config/kairos/prompts.json).

    Semeia do template empacotado se o arquivo não existir; em corrupção,
    ressemeia. Retorna sempre uma lista (vazia só se o template falhar).
    """
    if not _PROMPTS_PATH.exists():
        # Migração: usuários antigos tinham os prompts embutidos no config.json.
        # Preserva-os; senão, semeia do template empacotado.
        seed = _legacy_prompts_from_config() or _read_template_prompts()
        save_prompts(seed)
        return seed
    try:
        with open(_PROMPTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("prompts.json inválido")
        return data
    except Exception as e:
        logger.error(f"Erro ao ler prompts em {_PROMPTS_PATH}: {e} — ressemeando")
        seed = _read_template_prompts()
        save_prompts(seed)
        return seed


def save_prompts(prompts: list) -> None:
    _PROMPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(_PROMPTS_PATH, "w", encoding="utf-8") as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        logger.info(f"Prompts salvos em {_PROMPTS_PATH}")
    except Exception as e:
        logger.error(f"Erro ao salvar prompts: {e}")
        raise RuntimeError(f"Erro ao salvar prompts: {e}") from e
