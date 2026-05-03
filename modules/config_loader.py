"""Carrega arquivos YAML de configuração com cache."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent.parent / "config"


@lru_cache(maxsize=8)
def load_yaml(filename: str) -> dict:
    path = CONFIG_DIR / filename
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fontes_confiaveis() -> dict:
    return load_yaml("fontes_confiaveis.yml")


def parametros_np() -> dict:
    return load_yaml("parametros_np.yml")


def prompts() -> dict:
    return load_yaml("prompts.yml")
