"""
Sefaz CE 2026 — App de preparação para a Ariane.

Ponto de entrada do Streamlit. Estrutura de navegação:
- Estudante (Ariane): Dashboard, Simulado, Material de Estudo, Histórico
- Admin (Romel): tudo acima + Feedbacks da Ariane + Configurações

Para rodar localmente:
    streamlit run app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Garante que os módulos locais sejam importáveis
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from db.database import init_db
from db.models import PerfilUsuario
from modules.auth import exigir_login, logout
from modules.version import get_build_info


st.set_page_config(
    page_title="Sefaz CE 2026 — Preparação",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def _bootstrap():
    """Inicializa banco e seed na primeira execução do processo."""
    init_db()
    # Seed roda só se não houver disciplinas
    from db.database import get_session
    from db.models import Disciplina

    session = get_session()
    try:
        if session.query(Disciplina).count() == 0:
            from db.seed_edital import seed
            seed()
    finally:
        session.close()


_bootstrap()
user = exigir_login()


# ============================================================================
# Sidebar — navegação e usuário logado
# ============================================================================
with st.sidebar:
    st.markdown(f"### 👤 {user.nome}")
    st.caption(f"Perfil: **{user.perfil.value}**")
    if st.button("Sair", use_container_width=True):
        logout()
    st.divider()

    # Build info — admin only (info técnica de versionamento)
    if user.perfil == PerfilUsuario.ADMIN:
        build = get_build_info()
        st.caption(
            f"🛠️ **Build:** `{build.short_sha}` ({build.ref_name})  \n"
            f"📅 **Deploy:** {build.deploy_time.strftime('%d/%m %H:%M UTC') if build.deploy_time else '?'}"
        )


# ============================================================================
# Conteúdo principal — placeholder até as páginas serem construídas
# ============================================================================
st.title("📚 Sefaz CE 2026")
st.subheader("Preparação para a prova de 1–2 de agosto de 2026")

st.info(
    "🚧 **Aplicação em construção.** O esqueleto do app está pronto. "
    "As próximas etapas vão adicionar: Simulados, Material de Estudo e Dashboard."
)

with st.expander("✅ O que já está pronto"):
    st.markdown(
        """
        - Estrutura do projeto e dependências
        - Schema do banco de dados (SQLAlchemy)
        - Seed do edital — 13 disciplinas e ~290 sub-tópicos
        - Configurações: whitelist de fontes, parâmetros NP, prompts
        - Autenticação por login e senha
        - Sincronização automática de usuários do `secrets.toml`
        """
    )

with st.expander("📋 Próximas etapas"):
    st.markdown(
        """
        1. Motor de geração de questões (Claude API + RAG)
        2. Motor de cálculo da Nota Padronizada
        3. Tela de simulado (3 modos: por disciplina, áreas fracas, completo)
        4. Tela de resultado pós-simulado
        5. Motor de geração de material de estudo
        6. Dashboard gerencial
        7. Aba de feedbacks consolidados (admin)
        """
    )

# Mostra estrutura do edital — sanity check de que o seed funcionou
with st.expander("📖 Conteúdo do edital (Área A01) — disciplinas e pesos"):
    from db.database import get_session
    from db.models import BlocoEdital, Disciplina, SubTopico

    session = get_session()
    try:
        for bloco in [BlocoEdital.GERAIS, BlocoEdital.ESPECIFICOS]:
            label = "Conhecimentos Gerais (peso 1)" if bloco == BlocoEdital.GERAIS else "Conhecimentos Específicos (peso 2)"
            st.markdown(f"#### {label}")
            disciplinas = (
                session.query(Disciplina)
                .filter_by(bloco=bloco)
                .order_by(Disciplina.ordem)
                .all()
            )
            for d in disciplinas:
                n_sub = session.query(SubTopico).filter_by(disciplina_id=d.id).count()
                st.markdown(f"- **{d.nome}** — {d.n_questoes_prova} questões na prova, {n_sub} sub-tópicos")
    finally:
        session.close()


if user.perfil == PerfilUsuario.ADMIN:
    st.divider()
    st.caption("🛠️ Modo admin ativo (Romel). Aba de feedbacks da Ariane aparecerá aqui quando estiver pronta.")
