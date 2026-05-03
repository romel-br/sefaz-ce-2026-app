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
from modules.version import get_build_info


st.set_page_config(
    page_title="Calculadora NP — Sefaz CE 2026",
    page_icon="🧮",
    layout="wide",
)

user = exigir_login()

# Build info na sidebar
with st.sidebar:
    build = get_build_info()
    st.caption(
        f"🛠️ **Build:** `{build.short_sha}` ({build.ref_name})  \n"
        f"📅 **Deploy:** {build.deploy_time.strftime('%d/%m %H:%M UTC') if build.deploy_time else '?'}"
    )

st.title("🧮 Calculadora de Nota Padronizada")
st.caption(
    "Simule cenários de acertos para visualizar sua chance de aprovação. "
    "Fórmula oficial do edital (item 9.5)."
)

cfg = parametros_np()
total_g = cfg["conhecimentos_gerais"]["total_questoes"]
total_e = cfg["conhecimentos_especificos"]["total_questoes"]


# ============================================================================
# Inputs
# ============================================================================
st.subheader("Cenário")
col1, col2 = st.columns(2)

with col1:
    acertos_g = st.slider(
        f"Acertos em Conhecimentos Gerais (peso 1×)",
        min_value=0,
        max_value=total_g,
        value=40,
        help=f"Total: {total_g} questões. Média estimada do grupo: {cfg['conhecimentos_gerais']['media_acertos_grupo']}.",
    )
    pct_g = (acertos_g / total_g) * 100
    st.caption(f"= {pct_g:.0f}% de acerto")

with col2:
    acertos_e = st.slider(
        f"Acertos em Conhecimentos Específicos (peso 2×)",
        min_value=0,
        max_value=total_e,
        value=38,
        help=f"Total: {total_e} questões. Média estimada do grupo: {cfg['conhecimentos_especificos']['media_acertos_grupo']}.",
    )
    pct_e = (acertos_e / total_e) * 100
    st.caption(f"= {pct_e:.0f}% de acerto")


# ============================================================================
# Cálculo
# ============================================================================
r = calcular_score(acertos_gerais=acertos_g, acertos_especificos=acertos_e)

st.divider()

# ============================================================================
# Resultado — cartão grande de chance
# ============================================================================
st.subheader("Resultado")

# Cartão grande colorido
st.markdown(
    f"""
    <div style="
        background-color: {r.faixa.cor};
        color: white;
        padding: 24px;
        border-radius: 12px;
        text-align: center;
        margin: 16px 0;
    ">
        <div style="font-size: 48px; line-height: 1;">{r.faixa.emoji}</div>
        <div style="font-size: 28px; font-weight: bold; margin-top: 12px;">
            {r.faixa.nome}
        </div>
        <div style="font-size: 56px; font-weight: bold; margin: 16px 0;">
            {r.score_final:.1f} pts
        </div>
        <div style="font-size: 14px; opacity: 0.9;">
            {r.faixa.mensagem}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Detalhamento
col1, col2, col3 = st.columns(3)
col1.metric(
    "NP Gerais (peso 1×)",
    f"{r.np_gerais:.1f}",
    help=f"Fórmula: ((acertos - média) / DP) × 10 + 50 = (({acertos_g} - 40) / 10) × 10 + 50",
)
col2.metric(
    "NP Específicos (peso 2×)",
    f"{r.np_especificos:.1f}",
    help=f"Fórmula: (({acertos_e} - 38) / 12) × 10 + 50",
)
col3.metric(
    "Diferença para o corte (150)",
    f"{r.score_final - 150:+.1f}",
    delta=f"{r.score_final - 150:+.1f}",
    help="Negativo = abaixo do corte. Positivo = acima.",
)


# ============================================================================
# Visão das 4 faixas — onde você está
# ============================================================================
st.subheader("Faixas de chance")

for faixa in cfg["faixas"]:
    is_current = faixa["nome"] == r.faixa.nome
    border = "3px solid #000" if is_current else "1px solid #ddd"
    bg = faixa["cor"]
    st.markdown(
        f"""
        <div style="
            display: flex;
            align-items: center;
            background-color: {bg};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            border: {border};
            margin: 6px 0;
            font-size: 14px;
        ">
            <div style="font-size: 24px; margin-right: 12px;">{faixa['emoji']}</div>
            <div style="flex: 1;">
                <strong>{faixa['nome']}</strong> ({faixa['score_min']}–{faixa['score_max']} pts)
                {"  ← <strong>VOCÊ ESTÁ AQUI</strong>" if is_current else ""}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# Premissas e disclaimer
# ============================================================================
with st.expander("⚙️ Premissas e parâmetros utilizados"):
    st.markdown(
        f"""
        **Fórmula (edital, item 9.5):**
        `NP = ((Acertos - Média do grupo) / Desvio Padrão do grupo) × 10 + 50`

        **Score final:** `NP_Gerais × 1 + NP_Específicos × 2`

        **Corte de habilitação:** ≥ 150 pontos = candidato **mediano** do grupo.

        **Parâmetros estimados** (baseados em concursos FCC Sefaz anteriores):

        | Bloco | Total | Média estimada | DP estimado |
        |---|---|---|---|
        | Conhecimentos Gerais | {total_g} | {cfg['conhecimentos_gerais']['media_acertos_grupo']} | {cfg['conhecimentos_gerais']['desvio_padrao_grupo']} |
        | Conhecimentos Específicos | {total_e} | {cfg['conhecimentos_especificos']['media_acertos_grupo']} | {cfg['conhecimentos_especificos']['desvio_padrao_grupo']} |

        ⚠️ Médias e DPs são premissas — serão ajustadas quando dados reais do concurso atual surgirem.
        """
    )
