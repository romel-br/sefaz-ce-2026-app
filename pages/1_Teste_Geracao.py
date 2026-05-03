"""
Página de teste do motor de geração de questões.

Permite ao admin (Romel) selecionar disciplina + sub-tópico + quantidade
e gerar questões na hora pelo navegador, para validar a qualidade antes
de integrar com o fluxo de simulado.

Esta página NÃO persiste nada no banco — é só para teste/calibração.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from db.database import get_session
from db.models import BlocoEdital, Disciplina, PerfilUsuario, SubTopico
from modules.auth import exigir_login
from modules.question_generator import gerar_questoes
from modules.theme import (
    COLOR_ACCENT,
    COLOR_BORDER,
    COLOR_FAIXA_OK,
    COLOR_PRIMARY,
    apply_theme,
    subtitle,
)
from modules.version import get_build_info


st.set_page_config(
    page_title="Teste de Geração — Riri Auditora",
    page_icon="📖",
    layout="wide",
)

apply_theme()


# ============================================================================
# Auth — só admin acessa
# ============================================================================
user = exigir_login()
if user.perfil != PerfilUsuario.ADMIN:
    st.error("Acesso restrito ao admin.")
    st.stop()

# Build info na sidebar
with st.sidebar:
    build = get_build_info()
    deploy_str = (
        build.deploy_time.strftime("%d/%m %H:%M UTC")
        if build.deploy_time else "?"
    )
    st.caption(f"Build `{build.short_sha}` · {build.ref_name} · {deploy_str}")


# ============================================================================
# Header
# ============================================================================
st.title("Teste de geração")
subtitle("Calibração de qualidade · não persiste no banco")


# ============================================================================
# Seletor
# ============================================================================
session = get_session()
try:
    disciplinas = session.query(Disciplina).order_by(Disciplina.ordem).all()

    col1, col2 = st.columns([2, 1])

    with col1:
        disc_options = {d.nome: d for d in disciplinas}
        disc_nome = st.selectbox(
            "Disciplina",
            options=list(disc_options.keys()),
            help="Escolha a disciplina do edital A01.",
        )
        disciplina = disc_options[disc_nome]

        sub_topicos = (
            session.query(SubTopico)
            .filter_by(disciplina_id=disciplina.id)
            .order_by(SubTopico.ordem)
            .all()
        )
        sub_options = {s.nome: s for s in sub_topicos}
        sub_nome = st.selectbox(
            "Sub-tópico",
            options=list(sub_options.keys()),
            help="O sub-tópico específico para o qual gerar a questão.",
        )

    with col2:
        bloco_label = (
            "Conhecimentos Gerais" if disciplina.bloco == BlocoEdital.GERAIS
            else "Conhecimentos Específicos"
        )
        st.markdown(
            f"""
            <div class="card">
                <div class="card-section">
                    <div class="card-label">Bloco</div>
                    <div style="font-weight: 500;">{bloco_label}</div>
                </div>
                <div class="card-section">
                    <div class="card-label">Peso · Questões na prova</div>
                    <div style="font-family: 'Crimson Pro', serif; font-size: 1.3rem;
                                color: {COLOR_PRIMARY}; font-weight: 600;">
                        {disciplina.peso}× · {disciplina.n_questoes_prova}q
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        quantidade = st.number_input(
            "Quantas questões gerar",
            min_value=1, max_value=5, value=1,
            help="Recomendado 1-2 para testes rápidos. 5 leva ~2 min.",
        )

    st.write("")
    if st.button("Gerar questões", type="primary", use_container_width=True):
        with st.spinner(
            f"Gerando {quantidade} questão(ões) · 30-90s "
            "(thinking + web search + structured output)"
        ):
            try:
                result = gerar_questoes(
                    disciplina=disc_nome,
                    sub_topico=sub_nome,
                    bloco=bloco_label,
                    quantidade=int(quantidade),
                )
            except Exception as e:
                st.error(f"Erro na geração: {type(e).__name__}: {e}")
                st.exception(e)
                st.stop()

        # ====================================================================
        # Métricas
        # ====================================================================
        usage = result["usage"]
        cache_read = usage.get("cache_read_input_tokens", 0)
        cache_write = usage.get("cache_creation_input_tokens", 0)

        st.write("")
        with st.expander("Métricas e custo da chamada", expanded=False):
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            mcol1.metric("Input fresh", usage["input_tokens"])
            mcol2.metric("Cache write", cache_write)
            mcol3.metric("Cache read", cache_read, help="~10% do custo de input")
            mcol4.metric("Output", usage["output_tokens"])

            cost_input = usage["input_tokens"] * 5 / 1_000_000
            cost_cache_w = cache_write * 5 * 1.25 / 1_000_000
            cost_cache_r = cache_read * 5 * 0.1 / 1_000_000
            cost_output = usage["output_tokens"] * 25 / 1_000_000
            total = cost_input + cost_cache_w + cost_cache_r + cost_output
            st.caption(f"Custo desta chamada: ~US$ {total:.4f} · Modelo: {result['model']}")

        # ====================================================================
        # Cartões de questões
        # ====================================================================
        st.write("")
        for i, q in enumerate(result["questoes"], start=1):
            # Badge "Questão N" + enunciado em cartão
            st.markdown(
                f"""
                <div class="card" style="margin-top: 1.5rem;">
                    <div style="display: flex; justify-content: space-between;
                                align-items: baseline; margin-bottom: 1rem;">
                        <div style="font-family: 'Crimson Pro', serif;
                                    font-size: 1.4rem; font-weight: 600;
                                    color: {COLOR_PRIMARY};">
                            Questão {i}
                        </div>
                        <div class="card-label">
                            {disc_nome}
                        </div>
                    </div>
                    <div style="font-size: 1rem; line-height: 1.6;
                                margin-bottom: 1.5rem; color: #1a1a1a;">
                        {q['enunciado']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Alternativas — cartão verde sutil pra correta, neutro pras outras
            for letra in "ABCDE":
                if letra == q["gabarito"]:
                    st.markdown(
                        f"""
                        <div style="background: #f0f5ed;
                                    border-left: 3px solid {COLOR_FAIXA_OK};
                                    padding: 12px 16px;
                                    border-radius: 4px;
                                    margin: 6px 0;">
                            <strong style="color: {COLOR_FAIXA_OK};">({letra})</strong>
                            {q['alternativas'][letra]}
                            <span style="float: right; color: {COLOR_FAIXA_OK};
                                         font-size: 0.85rem; font-weight: 500;">
                                gabarito
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                        <div style="background: white;
                                    border: 1px solid {COLOR_BORDER};
                                    padding: 12px 16px;
                                    border-radius: 4px;
                                    margin: 6px 0;">
                            <strong>({letra})</strong> {q['alternativas'][letra]}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # Justificativa + fonte
            with st.expander(f"Justificativa e fonte"):
                st.markdown(f"**Justificativa**\n\n{q['justificativa']}")
                st.write("")
                st.markdown(f"**Fonte:** {q['fonte_descricao']}")
                if q.get("fonte_url"):
                    st.markdown(f"[Abrir fonte]({q['fonte_url']})")
                if q.get("alerta_revisao"):
                    st.warning("Esta questão precisa de revisão manual (fonte incerta).")

finally:
    session.close()
