"""
Tema visual centralizado — CSS injetado no Streamlit.

Direção de design:
- Editorial/profissional, não techbro
- Crimson Pro (serif) para títulos + Inter para corpo
- Paleta: navy #1e3a5f + creme #fafaf7 + terracota #c2563f
- Cartões com sombra sutil em vez de bordas duras
- Sem purple gradients, sem rounded-uniforms exagerados

Uso: chamar `apply_theme()` no início de cada página, antes de renderizar.
"""
from __future__ import annotations

import streamlit as st

# Paleta — espelha o config.toml mas exposta para uso em CSS/components
COLOR_PRIMARY = "#1e3a5f"
COLOR_PRIMARY_LIGHT = "#2d5485"
COLOR_BG = "#fafaf7"
COLOR_SAND = "#f0ede4"
COLOR_INK = "#1a1a1a"
COLOR_MUTED = "#6b6b6b"
COLOR_ACCENT = "#c2563f"        # Terracota — destaques, CTAs secundários
COLOR_BORDER = "#e8e3d6"        # Sand mais escuro — divisórias suaves

# Faixas (usadas no cartão de chance da Calculadora NP)
COLOR_FAIXA_PERIGO = "#a8392b"  # Vermelho terra
COLOR_FAIXA_ALERTA = "#c2563f"  # Terracota
COLOR_FAIXA_ATENCAO = "#a17e2a" # Mostarda escura
COLOR_FAIXA_OK = "#3d6b3d"      # Verde mato


_CSS = f"""
<style>
/* === Google Fonts === */
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

/* === Tipografia === */
html, body, [class*="st-"], [class*="css-"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: {COLOR_INK};
}}

h1, h2, h3, h4, h5, h6, .stHeading {{
    font-family: 'Crimson Pro', Georgia, serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    color: {COLOR_PRIMARY};
}}

h1 {{ font-size: 2.4rem !important; line-height: 1.15 !important; }}
h2 {{ font-size: 1.8rem !important; }}
h3 {{ font-size: 1.4rem !important; }}

/* Subtítulo logo abaixo do título */
.subtitle {{
    font-family: 'Crimson Pro', Georgia, serif;
    font-style: italic;
    font-size: 1.15rem;
    color: {COLOR_MUTED};
    margin-top: -0.5rem;
    margin-bottom: 1.5rem;
}}

/* === Background === */
.stApp {{
    background-color: {COLOR_BG};
}}

/* Sidebar com cor sand mais visível */
[data-testid="stSidebar"] {{
    background-color: {COLOR_SAND};
    border-right: 1px solid {COLOR_BORDER};
}}

/* === Cartões customizados === */
.card {{
    background: white;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    margin: 0.5rem 0;
    box-shadow: 0 1px 3px rgba(30, 58, 95, 0.04);
}}

.card-section {{
    margin-bottom: 1rem;
}}

.card-section:last-child {{
    margin-bottom: 0;
}}

.card-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {COLOR_MUTED};
    margin-bottom: 0.25rem;
}}

/* === Botões === */
.stButton > button {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    border: 1px solid {COLOR_BORDER} !important;
    transition: all 0.15s ease;
}}

.stButton > button[kind="primary"] {{
    background-color: {COLOR_PRIMARY} !important;
    border-color: {COLOR_PRIMARY} !important;
    color: white !important;
}}

.stButton > button[kind="primary"]:hover {{
    background-color: {COLOR_PRIMARY_LIGHT} !important;
    border-color: {COLOR_PRIMARY_LIGHT} !important;
}}

/* === Inputs === */
.stTextInput input, .stNumberInput input, .stSelectbox > div {{
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
}}

/* === Expanders mais elegantes === */
.streamlit-expanderHeader {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    color: {COLOR_PRIMARY} !important;
}}

/* === Métricas: tipografia diferenciada === */
[data-testid="stMetric"] {{
    background: white;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 0.75rem 1rem;
}}

[data-testid="stMetricLabel"] {{
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {COLOR_MUTED} !important;
}}

[data-testid="stMetricValue"] {{
    font-family: 'Crimson Pro', Georgia, serif !important;
    font-size: 1.8rem !important;
    color: {COLOR_PRIMARY} !important;
    font-weight: 600 !important;
}}

/* === Slider === */
.stSlider [data-baseweb="slider"] [role="slider"] {{
    background-color: {COLOR_PRIMARY} !important;
}}

/* === Caption (texto pequeno) === */
[data-testid="stCaptionContainer"] {{
    color: {COLOR_MUTED} !important;
    font-size: 0.85rem;
}}

/* === Divider mais sutil === */
[data-testid="stMarkdownContainer"] hr {{
    margin: 2rem 0 !important;
    border-color: {COLOR_BORDER} !important;
}}

/* === Alertas (info, success, error, warning) === */
.stAlert {{
    border-radius: 6px !important;
    border: none !important;
}}

/* === Sidebar — caption do build menos intrusivo === */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
    font-size: 0.7rem !important;
    opacity: 0.7;
}}

/* === Esconde footer Streamlit (cleaner) === */
footer {{
    visibility: hidden;
}}

/* === Botão de colapsar/expandir sidebar — mais visível === */
/* Quando sidebar está expandida: botão de colapso no topo */
[data-testid="stSidebarCollapseButton"] button,
button[kind="headerNoPadding"][data-testid="stBaseButton-headerNoPadding"] {{
    background-color: {COLOR_PRIMARY} !important;
    color: white !important;
    border-radius: 50% !important;
    width: 32px !important;
    height: 32px !important;
    box-shadow: 0 2px 6px rgba(30, 58, 95, 0.2) !important;
    transition: all 0.2s ease !important;
}}

[data-testid="stSidebarCollapseButton"] button:hover,
button[kind="headerNoPadding"][data-testid="stBaseButton-headerNoPadding"]:hover {{
    background-color: {COLOR_PRIMARY_LIGHT} !important;
    transform: scale(1.05);
}}

/* Quando sidebar colapsada: botão flutuante para abrir */
[data-testid="stSidebarCollapsedControl"] button {{
    background-color: {COLOR_PRIMARY} !important;
    color: white !important;
    border-radius: 0 8px 8px 0 !important;
    padding: 8px 12px !important;
    box-shadow: 2px 2px 8px rgba(30, 58, 95, 0.25) !important;
}}

/* === Reduz padding superior do main pra dar mais respiro === */
.main .block-container {{
    padding-top: 2rem !important;
    max-width: 1200px;
}}
</style>
"""


def apply_theme():
    """Injeta o CSS do tema. Chamar no início de cada página."""
    st.markdown(_CSS, unsafe_allow_html=True)


def subtitle(text: str):
    """Renderiza subtítulo italic abaixo do título principal."""
    st.markdown(f'<p class="subtitle">{text}</p>', unsafe_allow_html=True)


def card(content: str):
    """Renderiza um cartão branco com sombra sutil. content é HTML."""
    st.markdown(f'<div class="card">{content}</div>', unsafe_allow_html=True)
