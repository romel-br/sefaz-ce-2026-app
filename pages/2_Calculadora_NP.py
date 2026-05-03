"""
Calculadora interativa da Nota Padronizada.

Permite simular cenários: digita acertos hipotéticos por bloco e vê
em tempo real a NP, o score final e a faixa de chance de aprovação.

Útil pra:
- Ariane: visualizar "se eu acertar X em específicos, minha chance vai pra Y"
- Romel: validar a matemática e ajustar parâmetros se necessário
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from modules.auth import exigir_login
from modules.config_loader import parametros_np
from modules.np_calculator import calcular_score
from modules.theme import COLOR_BORDER, COLOR_MUTED, COLOR_PRIMARY, apply_theme, subtitle
from modules.version import get_build_info


st.set_page_config(
    page_title="Calculadora NP — Riri Auditora",
    page_icon="📖",
    layout="wide",
)

apply_theme()

user = exigir_login()

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
st.title("Calculadora de Nota Padronizada")
subtitle("Simule cenários de acertos · fórmula oficial do edital, item 9.5")


cfg = parametros_np()
total_g = cfg["conhecimentos_gerais"]["total_questoes"]
total_e = cfg["conhecimentos_especificos"]["total_questoes"]


# ============================================================================
# Inputs
# ============================================================================
st.markdown("### Cenário hipotético")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""
        <div style="margin-bottom: 8px;">
            <span style="font-family: 'Crimson Pro', serif; font-size: 1.1rem;
                         color: {COLOR_PRIMARY}; font-weight: 600;">
                Conhecimentos Gerais
            </span>
            <span style="color: {COLOR_MUTED}; font-size: 0.85rem; margin-left: 8px;">
                · peso 1× · média do grupo: {cfg['conhecimentos_gerais']['media_acertos_grupo']}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    acertos_g = st.slider(
        "Acertos em Gerais",
        min_value=0,
        max_value=total_g,
        value=40,
        label_visibility="collapsed",
    )
    pct_g = (acertos_g / total_g) * 100
    st.caption(f"{acertos_g} de {total_g} questões · {pct_g:.0f}% de acerto")

with col2:
    st.markdown(
        f"""
        <div style="margin-bottom: 8px;">
            <span style="font-family: 'Crimson Pro', serif; font-size: 1.1rem;
                         color: {COLOR_PRIMARY}; font-weight: 600;">
                Conhecimentos Específicos
            </span>
            <span style="color: {COLOR_MUTED}; font-size: 0.85rem; margin-left: 8px;">
                · peso 2× · média do grupo: {cfg['conhecimentos_especificos']['media_acertos_grupo']}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    acertos_e = st.slider(
        "Acertos em Específicos",
        min_value=0,
        max_value=total_e,
        value=38,
        label_visibility="collapsed",
    )
    pct_e = (acertos_e / total_e) * 100
    st.caption(f"{acertos_e} de {total_e} questões · {pct_e:.0f}% de acerto")


# ============================================================================
# Cálculo
# ============================================================================
r = calcular_score(acertos_gerais=acertos_g, acertos_especificos=acertos_e)


# ============================================================================
# Cartão de resultado — visual editorial, não SaaS
# ============================================================================
st.write("")
st.markdown(
    f"""
    <div class="card" style="
        background: linear-gradient(135deg, {r.faixa.cor} 0%, {r.faixa.cor}dd 100%);
        color: white;
        padding: 32px;
        text-align: center;
        border: none;
        box-shadow: 0 4px 16px rgba(30, 58, 95, 0.12);
    ">
        <div style="font-family: 'Crimson Pro', serif; font-size: 1.1rem;
                    opacity: 0.9; letter-spacing: 0.04em; text-transform: uppercase;
                    margin-bottom: 12px;">
            Sua chance no cenário atual
        </div>
        <div style="font-family: 'Crimson Pro', serif; font-size: 2.4rem;
                    font-weight: 600; margin-bottom: 4px;">
            {r.faixa.nome}
        </div>
        <div style="font-family: 'Crimson Pro', serif; font-size: 4.5rem;
                    font-weight: 700; line-height: 1; margin: 16px 0;">
            {r.score_final:.0f}
            <span style="font-size: 1.5rem; opacity: 0.7;">pontos</span>
        </div>
        <div style="font-style: italic; opacity: 0.95; max-width: 480px;
                    margin: 0 auto; line-height: 1.5;">
            {r.faixa.mensagem}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# Detalhamento
# ============================================================================
st.write("")
col1, col2, col3 = st.columns(3)
col1.metric(
    "NP Gerais",
    f"{r.np_gerais:.1f}",
    help=f"(({acertos_g} − 40) ÷ 10) × 10 + 50",
)
col2.metric(
    "NP Específicos",
    f"{r.np_especificos:.1f}",
    help=f"(({acertos_e} − 38) ÷ 12) × 10 + 50",
)
delta = r.score_final - 150
col3.metric(
    "Distância para o corte",
    f"{delta:+.1f}",
    delta=f"{delta:+.1f}",
    help="Negativo: abaixo do corte. Positivo: acima.",
)


# ============================================================================
# Visão das 4 faixas
# ============================================================================
st.write("")
st.markdown("### As quatro faixas de chance")

for faixa in cfg["faixas"]:
    is_current = faixa["nome"] == r.faixa.nome
    bg = faixa["cor"]
    opacity = "1" if is_current else "0.55"
    indicator = (
        '<span style="float: right; font-weight: 600;">' "▸ você está aqui</span>"
        if is_current else ""
    )
    st.markdown(
        f"""
        <div style="
            background-color: {bg};
            color: white;
            padding: 14px 20px;
            border-radius: 6px;
            margin: 6px 0;
            opacity: {opacity};
            transition: opacity 0.2s ease;
            box-shadow: {'0 2px 6px rgba(0,0,0,0.1)' if is_current else 'none'};
        ">
            <strong>{faixa['nome']}</strong>
            <span style="opacity: 0.85; font-size: 0.9rem; margin-left: 12px;">
                {faixa['score_min']}–{faixa['score_max']} pontos
            </span>
            {indicator}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# Premissas e disclaimer
# ============================================================================
with st.expander("Premissas e parâmetros utilizados"):
    st.markdown(
        f"""
        **Fórmula oficial (edital, item 9.5):**

        `NP = ((Acertos − Média do grupo) ÷ Desvio Padrão do grupo) × 10 + 50`

        **Score final:** `NP_Gerais × 1 + NP_Específicos × 2`

        **Corte de habilitação:** ≥ 150 pontos = candidato **mediano** do grupo.
        Para passar, é necessário estar acima da mediana.

        **Parâmetros estimados** (baseados em concursos FCC Sefaz anteriores):

        | Bloco | Total | Média estimada | DP estimado |
        |---|---|---|---|
        | Conhecimentos Gerais | {total_g} | {cfg['conhecimentos_gerais']['media_acertos_grupo']} | {cfg['conhecimentos_gerais']['desvio_padrao_grupo']} |
        | Conhecimentos Específicos | {total_e} | {cfg['conhecimentos_especificos']['media_acertos_grupo']} | {cfg['conhecimentos_especificos']['desvio_padrao_grupo']} |

        Médias e DPs são premissas — serão ajustadas quando dados reais
        do concurso atual surgirem.
        """
    )
