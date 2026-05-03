"""
Configuração da conexão com o banco de dados.
Suporta SQLite local (dev) e Turso/libSQL (produção via DATABASE_URL).
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base


def _get_database_url() -> str:
    """Resolve a URL do banco a partir de secrets do Streamlit ou env var."""
    try:
        url = st.secrets.get("DATABASE_URL")
        if url:
            return url
    except (FileNotFoundError, KeyError):
        pass

    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    default_path = Path(__file__).parent / "local.db"
    return f"sqlite:///{default_path}"


_engine = None
_SessionLocal: sessionmaker | None = None


def get_engine():
    global _engine
    if _engine is None:
        url = _get_database_url()
        is_libsql = "libsql" in url
        is_sqlite_local = url.startswith("sqlite:") and not is_libsql

        connect_args: dict = {}
        if is_sqlite_local:
            connect_args["check_same_thread"] = False

        engine_kwargs: dict = {"connect_args": connect_args, "echo": False}

        # libSQL/Turso não suporta `PRAGMA read_uncommitted` que o SQLAlchemy
        # invoca para detectar isolation level. Setamos AUTOCOMMIT para pular essa fase.
        if is_libsql:
            engine_kwargs["isolation_level"] = "AUTOCOMMIT"

        _engine = create_engine(url, **engine_kwargs)
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


def get_session() -> Session:
    return get_session_factory()()


def init_db() -> None:
    """Cria todas as tabelas se ainda não existirem."""
    Base.metadata.create_all(get_engine())


def reset_db() -> None:
    """⚠️ APAGA TUDO. Use só em dev."""
    Base.metadata.drop_all(get_engine())
    Base.metadata.create_all(get_engine())
