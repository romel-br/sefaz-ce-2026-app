"""
Configuração da conexão com o banco de dados.
Suporta SQLite local (dev) e PostgreSQL (produção via DATABASE_URL — Neon).
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

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
        connect_args = {"check_same_thread": False} if url.startswith("sqlite:") else {}
        # pool_pre_ping para sobreviver ao auto-pause do Neon free tier
        _engine = create_engine(
            url,
            connect_args=connect_args,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=300,
        )
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


def get_session() -> Session:
    """Retorna uma session sem context manager (caller controla close)."""
    return get_session_factory()()


@contextmanager
def db_session() -> Iterator[Session]:
    """
    Context manager para session — garante close, com rollback automático em erro.
    Caller controla commit explicitamente (não há auto-commit).

    Uso:
        with db_session() as s:
            s.query(Foo).all()
            s.commit()  # explícito
    """
    session = get_session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Cria todas as tabelas se ainda não existirem."""
    Base.metadata.create_all(get_engine())


def reset_db() -> None:
    """⚠️ APAGA TUDO. Use só em dev."""
    Base.metadata.drop_all(get_engine())
    Base.metadata.create_all(get_engine())
