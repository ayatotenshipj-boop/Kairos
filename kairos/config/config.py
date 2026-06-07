import json
import logging
from pathlib import Path

from kairos.config.defaults import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path.home() / ".config" / "kairos" / "config.json"


def load() -> dict:
    if not _CONFIG_PATH.exists():
        logger.info("Config não encontrado, criando com padrões")
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        save(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        config = dict(DEFAULT_CONFIG)
        config.update(data)
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
