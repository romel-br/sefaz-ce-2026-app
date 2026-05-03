"""
Autenticação simples baseada em bcrypt + secrets.toml + session_state.

Os usuários e seus hashes de senha ficam em .streamlit/secrets.toml na seção [users.X].
Para gerar um hash novo:
    python -c "import bcrypt; print(bcrypt.hashpw(b'sua_senha', bcrypt.gensalt()).decode())"
"""
from __future__ import annotations

from dataclasses import dataclass

import bcrypt
import streamlit as st

from db.database import get_session
from db.models import PerfilUsuario, Usuario


@dataclass
class UsuarioLogado:
    id: int
    username: str
    nome: str
    perfil: PerfilUsuario


def _carregar_usuarios_dos_secrets() -> dict[str, dict]:
    """Lê seção [users.X] do secrets.toml. Retorna {} se não houver."""
    try:
        users = st.secrets.get("users", {})
    except (FileNotFoundError, KeyError):
        return {}
    return dict(users) if users else {}


def _normalizar_username(username: str) -> str:
    """Normaliza username: lowercase + sem espaços extras."""
    return username.strip().lower()


def _sincronizar_usuarios_para_db():
    """Garante que os usuários do secrets existam na tabela usuarios."""
    secrets_users = _carregar_usuarios_dos_secrets()
    if not secrets_users:
        return

    from db.database import db_session  # noqa: PLC0415
    with db_session() as session:
        for username_raw, dados in secrets_users.items():
            # Normaliza ao inserir/atualizar (defesa contra typos no TOML)
            username = _normalizar_username(username_raw)
            existente = session.query(Usuario).filter_by(username=username).first()
            if existente:
                if existente.senha_hash != dados["senha_hash"]:
                    existente.senha_hash = dados["senha_hash"]
                if existente.nome != dados["nome"]:
                    existente.nome = dados["nome"]
                if existente.perfil.value != dados["perfil"]:
                    existente.perfil = PerfilUsuario(dados["perfil"])
            else:
                session.add(
                    Usuario(
                        username=username,
                        nome=dados["nome"],
                        senha_hash=dados["senha_hash"],
                        perfil=PerfilUsuario(dados["perfil"]),
                    )
                )
        session.commit()


def _verificar_senha(senha_plain: str, hash_armazenado: str) -> bool:
    try:
        return bcrypt.checkpw(senha_plain.encode(), hash_armazenado.encode())
    except (ValueError, TypeError):
        return False


def login_form() -> UsuarioLogado | None:
    """Renderiza o formulário de login. Retorna o usuário se autenticado."""
    _sincronizar_usuarios_para_db()

    if "usuario_logado" in st.session_state:
        return st.session_state["usuario_logado"]

    # Build info no topo (visível antes do login — útil para debug)
    try:
        from modules.version import get_build_info  # noqa: PLC0415
        build = get_build_info()
        deploy_str = (
            build.deploy_time.strftime("%d/%m %H:%M UTC")
            if build.deploy_time else "?"
        )
        st.caption(
            f"Build `{build.short_sha}` · {build.ref_name} · deploy {deploy_str}"
        )
    except Exception:
        pass

    st.markdown("## Riri Auditora")
    st.caption("Preparação para o concurso Sefaz CE 2026")

    with st.form("form_login"):
        username = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        enviar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

    if not enviar:
        return None

    from db.database import db_session  # noqa: PLC0415
    with db_session() as session:
        usuario = session.query(Usuario).filter_by(
            username=_normalizar_username(username)
        ).first()
        if not usuario or not _verificar_senha(senha, usuario.senha_hash):
            st.error("Usuário ou senha inválidos.")
            return None

        ul = UsuarioLogado(
            id=usuario.id,
            username=usuario.username,
            nome=usuario.nome,
            perfil=usuario.perfil,
        )
        st.session_state["usuario_logado"] = ul
        st.rerun()

    return None


def logout():
    st.session_state.pop("usuario_logado", None)
    st.rerun()


def usuario_atual() -> UsuarioLogado | None:
    return st.session_state.get("usuario_logado")


def exigir_login() -> UsuarioLogado:
    """Bloqueia a página se não houver usuário logado."""
    user = login_form()
    if user is None:
        st.stop()
    return user
