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
from datetime import date
from pathlib import Path

# Garante que os módulos locais sejam importáveis
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from db.database import init_db
from db.models import PerfilUsuario
from modules.auth import exigir_login, logout
from modules.theme import COLOR_ACCENT, COLOR_PRIMARY, apply_theme, subtitle
from modules.version import get_build_info


st.set_page_config(
    page_title="Riri Auditora — Sefaz CE 2026",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="auto",  # auto: expandida no desktop, colapsada no mobile
)

apply_theme()


@st.cache_resource
def _bootstrap():
    """Inicializa banco e seed na primeira execução do processo."""
    init_db()
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
# Sidebar
# ============================================================================
with st.sidebar:
    st.caption("Use a seta no topo para recolher este menu →")
    st.markdown(
        f"""
        <div style="margin-bottom: 1rem;">
            <div style="font-family: 'Crimson Pro', serif; font-size: 1.3rem;
                        color: {COLOR_PRIMARY}; font-weight: 600; line-height: 1;">
                {user.nome}
            </div>
            <div style="font-size: 0.75rem; color: #6b6b6b; text-transform: uppercase;
                        letter-spacing: 0.06em; margin-top: 4px;">
                {user.perfil.value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Sair", use_container_width=True):
        logout()

    st.divider()

    # Build info — admin only
    if user.perfil == PerfilUsuario.ADMIN:
        build = get_build_info()
        deploy_str = (
            build.deploy_time.strftime("%d/%m %H:%M UTC")
            if build.deploy_time else "?"
        )
        st.caption(f"Build `{build.short_sha}` · {build.ref_name} · {deploy_str}")


# ============================================================================
# Conteúdo principal
# ============================================================================
st.title("Riri Auditora")
subtitle("Preparação para o concurso Sefaz CE 2026 — Auditor-Fiscal, Área A01")


# Contagem regressiva pra prova
PROVA_DIA = date(2026, 8, 1)
hoje = date.today()
dias_restantes = (PROVA_DIA - hoje).days

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-label">Dias até a prova</div>
            <div style="font-family: 'Crimson Pro', serif; font-size: 3rem;
                        font-weight: 600; color: {COLOR_PRIMARY}; line-height: 1;">
                {dias_restantes}
            </div>
            <div style="color: #6b6b6b; margin-top: 8px;">
                Prova objetiva: 1 e 2 de agosto de 2026
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-label">Banca</div>
            <div style="font-family: 'Crimson Pro', serif; font-size: 1.5rem;
                        font-weight: 600; color: {COLOR_PRIMARY};">
                FCC
            </div>
            <div style="color: #6b6b6b; font-size: 0.85rem; margin-top: 4px;">
                Fundação Carlos Chagas
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-label">Corte de habilitação</div>
            <div style="font-family: 'Crimson Pro', serif; font-size: 1.5rem;
                        font-weight: 600; color: {COLOR_ACCENT};">
                ≥ 150 pts
            </div>
            <div style="color: #6b6b6b; font-size: 0.85rem; margin-top: 4px;">
                Acima da mediana
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.write("")  # spacing

# Aviso de construção — mais discreto
st.info(
    "Aplicação em construção iterativa. Use o menu lateral para acessar "
    "as funcionalidades já disponíveis. Novas serão adicionadas a cada release."
)

# ============================================================================
# Conteúdo do edital — apresentação mais elegante
# ============================================================================
st.markdown("### Estrutura do edital")
st.caption("Área A01 — Gestão Fazendária. 160 questões objetivas no total.")

import html as _html

from sqlalchemy import func

from db.database import db_session
from db.models import BlocoEdital, Disciplina, SubTopico

# #5: 1 query agregada em vez de N+1 (1 SELECT + 1 SELECT em vez de 14)
with db_session() as session:
    disciplinas = (
        session.query(Disciplina)
        .order_by(Disciplina.ordem)
        .all()
    )
    sub_count_rows = (
        session.query(SubTopico.disciplina_id, func.count(SubTopico.id))
        .group_by(SubTopico.disciplina_id)
        .all()
    )
    sub_count_por_disc = dict(sub_count_rows)

    # Snapshot serializável (objetos SQLAlchemy não funcionam após session.close)
    disc_snapshot = [
        {
            "id": d.id,
            "nome": d.nome,
            "bloco": d.bloco,
            "n_questoes_prova": d.n_questoes_prova,
            "n_sub_topicos": sub_count_por_disc.get(d.id, 0),
        }
        for d in disciplinas
    ]


def _render_disciplina(d: dict):
    nome_safe = _html.escape(d["nome"])
    st.markdown(
        f"""
        <div style="padding: 8px 0; border-bottom: 1px solid #e8e3d6;">
            <div style="font-weight: 500;">{nome_safe}</div>
            <div style="font-size: 0.8rem; color: #6b6b6b;">
                {d['n_questoes_prova']} questões · {d['n_sub_topicos']} sub-tópicos
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


col_g, col_e = st.columns(2)

with col_g:
    st.markdown(
        """
        <div style="font-family: 'Crimson Pro', serif; font-size: 1.2rem;
                    color: #1e3a5f; margin-bottom: 4px;">
            Conhecimentos Gerais
        </div>
        <div class="card-label">80 questões · peso 1×</div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    for d in disc_snapshot:
        if d["bloco"] == BlocoEdital.GERAIS:
            _render_disciplina(d)

with col_e:
    st.markdown(
        """
        <div style="font-family: 'Crimson Pro', serif; font-size: 1.2rem;
                    color: #1e3a5f; margin-bottom: 4px;">
            Conhecimentos Específicos
        </div>
        <div class="card-label">80 questões · peso 2×</div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    for d in disc_snapshot:
        if d["bloco"] == BlocoEdital.ESPECIFICOS:
            _render_disciplina(d)


# ============================================================================
# Roadmap (admin only) — info técnica do que vem por aí
# ============================================================================
if user.perfil == PerfilUsuario.ADMIN:
    st.write("")
    st.write("")
    with st.expander("Roadmap técnico"):
        st.markdown(
            """
            **Concluídos:**
            - Schema do banco + seed do edital (13 disciplinas, ~290 sub-tópicos)
            - Auth com bcrypt + secrets
            - Motor de geração de questões estilo FCC (Claude API + web_search)
            - Motor de cálculo da Nota Padronizada (4 faixas de chance)

            **Em construção:**
            - Telas de simulado (por disciplina · áreas fracas · completo)
            - Material de estudo gerado pós-simulado
            - Dashboard de proficiência por disciplina
            - Aba de feedbacks consolidados
            """
        )
