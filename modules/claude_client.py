"""
Cliente Anthropic configurado a partir de secrets.toml ou env var.

Uso:
    from modules.claude_client import get_client
    client = get_client()
    response = client.messages.create(...)
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import anthropic


def _load_api_key_from_secrets() -> str | None:
    """Lê ANTHROPIC_API_KEY do .streamlit/secrets.toml se rodando local."""
    secrets_path = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return None
    try:
        import tomllib
    except ImportError:  # Python < 3.11
        import tomli as tomllib
    with open(secrets_path, "rb") as f:
        data = tomllib.load(f)
    return data.get("ANTHROPIC_API_KEY")


def _resolve_api_key() -> str:
    """Resolve API key: secrets.toml local > env var. Stream secrets ainda não suportado fora do Streamlit."""
    # Tenta env var primeiro (mais comum em produção/scripts)
    if key := os.environ.get("ANTHROPIC_API_KEY"):
        return key

    # Se rodando dentro do Streamlit, tenta st.secrets
    try:
        import streamlit as st  # noqa: PLC0415
        try:
            if key := st.secrets.get("ANTHROPIC_API_KEY"):
                return key
        except (FileNotFoundError, KeyError):
            pass
    except ImportError:
        pass

    # Fallback: ler secrets.toml diretamente (útil em scripts locais)
    if key := _load_api_key_from_secrets():
        return key

    raise RuntimeError(
        "ANTHROPIC_API_KEY não encontrada. "
        "Defina como variável de ambiente ou adicione em .streamlit/secrets.toml"
    )


@lru_cache(maxsize=1)
def get_client() -> anthropic.Anthropic:
    """Singleton do cliente Anthropic."""
    return anthropic.Anthropic(api_key=_resolve_api_key())
