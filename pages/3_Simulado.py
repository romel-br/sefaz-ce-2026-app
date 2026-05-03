"""
Página principal de simulado — modo "por disciplina" (Iter 1 do Step 6).

Estados controlados via st.session_state["sim_state"]:
- "selecao": tela inicial (escolhe disciplina + preset + timer)
- "execucao": rodando o simulado (1 questão por vez, painel lateral)
- "resultado": tela pós-finalização

Fluxo:
1. Usuário entra → se há simulado em andamento, oferece retomar/descartar
2. Se não, mostra tela de seleção
3. Ao clicar "Iniciar", gera questões em paralelo (com progress bar)
4. Renderiza execução
5. Ao finalizar, mostra resultado
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from db.database import get_session
from db.models import Disciplina
from modules.auth import exigir_login
from modules.config_loader import parametros_np
from modules.simulado_engine import (
    descartar_simulado,
    finalizar_simulado,
    get_simulado_completo,
    iniciar_simulado_por_disciplina,
    responder_questao,
    simulado_em_andamento,
)
from modules.theme import (
    COLOR_ACCENT,
    COLOR_BORDER,
    COLOR_FAIXA_OK,
    COLOR_MUTED,
    COLOR_PRIMARY,
    apply_theme,
    subtitle,
)
from modules.version import get_build_info


st.set_page_config(
    page_title="Simulado — Riri Auditora",
    page_icon="📝",
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
# Estado inicial
# ============================================================================
if "sim_state" not in st.session_state:
    st.session_state.sim_state = "selecao"
if "sim_id" not in st.session_state:
    st.session_state.sim_id = None
if "sim_questao_idx" not in st.session_state:
    st.session_state.sim_questao_idx = 0
if "sim_inicio_ts" not in st.session_state:
    st.session_state.sim_inicio_ts = None


def _reset_session():
    st.session_state.sim_state = "selecao"
    st.session_state.sim_id = None
    st.session_state.sim_questao_idx = 0
    st.session_state.sim_inicio_ts = None


# ============================================================================
# Verifica simulado em andamento (no banco) — só se não estamos já em um
# ============================================================================
if st.session_state.sim_state == "selecao" and st.session_state.sim_id is None:
    em_andamento = simulado_em_andamento(user.id)
    if em_andamento:
        st.title("Você tem um simulado em andamento")
        subtitle(
            f"Iniciado em {em_andamento.iniciado_em.strftime('%d/%m/%Y %H:%M')} · "
            f"{em_andamento.n_questoes} questões"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Retomar simulado", type="primary", use_container_width=True):
                st.session_state.sim_id = em_andamento.id
                st.session_state.sim_state = "execucao"
                st.session_state.sim_inicio_ts = em_andamento.iniciado_em.timestamp()
                st.session_state.sim_questao_idx = 0
                st.rerun()
        with col2:
            if st.button("Descartar e começar outro", use_container_width=True):
                descartar_simulado(em_andamento.id)
                _reset_session()
                st.rerun()
        st.stop()


# ============================================================================
# ESTADO 1: SELEÇÃO
# ============================================================================
if st.session_state.sim_state == "selecao":
    st.title("Novo simulado")
    subtitle("Modo por disciplina · escolha a disciplina e o tamanho")

    cfg = parametros_np()
    presets = cfg["simulados"]["presets_curtos"]

    session = get_session()
    try:
        disciplinas = session.query(Disciplina).order_by(Disciplina.ordem).all()
        disc_options = {d.nome: d for d in disciplinas}
    finally:
        session.close()

    col1, col2 = st.columns([2, 1])

    with col1:
        disc_nome = st.selectbox("Disciplina", options=list(disc_options.keys()))
        disciplina = disc_options[disc_nome]

        st.write("")
        st.markdown("**Tamanho do simulado**")

        preset_keys = list(presets.keys())
        preset_labels = [
            f"{p['nome']} · {p['questoes']} questões · ~{p['tempo_minutos']} min"
            for p in presets.values()
        ]
        preset_idx = st.radio(
            "Tamanho",
            options=range(len(preset_keys)),
            format_func=lambda i: preset_labels[i],
            label_visibility="collapsed",
            index=1,  # Médio default
        )
        preset_key = preset_keys[preset_idx]
        preset = presets[preset_key]

    with col2:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-section">
                    <div class="card-label">Disciplina</div>
                    <div style="font-weight: 500;">{disciplina.nome}</div>
                </div>
                <div class="card-section">
                    <div class="card-label">Tamanho</div>
                    <div style="font-family: 'Crimson Pro', serif; font-size: 1.5rem;
                                color: {COLOR_PRIMARY}; font-weight: 600;">
                        {preset['questoes']} questões
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        com_timer = st.checkbox(
            "Ativar timer",
            value=False,
            help=f"Limita a {preset['tempo_minutos']} min, igual à prova real.",
        )

    st.write("")
    st.info(
        f"Ao iniciar, o sistema vai gerar {preset['questoes']} questões inéditas "
        "via Claude API. Geração em paralelo (até 5 simultâneas) leva ~3-5 minutos."
    )

    if st.button("Iniciar simulado", type="primary", use_container_width=True):
        # Geração com progress bar
        progress_bar = st.progress(0.0, text="Iniciando geração...")
        status_text = st.empty()

        def on_progress(p):
            progress_bar.progress(
                p.pct,
                text=(
                    f"Gerando questões: {p.concluidas}/{p.total} prontas"
                    + (f" ({p.falhas} falharam)" if p.falhas else "")
                ),
            )

        try:
            simulado = iniciar_simulado_por_disciplina(
                usuario_id=user.id,
                disciplina_id=disciplina.id,
                n_questoes=preset["questoes"],
                com_timer=com_timer,
                tempo_limite_segundos=preset["tempo_minutos"] * 60 if com_timer else None,
                progresso_callback=on_progress,
            )
        except Exception as e:
            st.error(f"Erro: {type(e).__name__}: {e}")
            st.exception(e)
            st.stop()

        progress_bar.empty()
        status_text.empty()

        st.session_state.sim_id = simulado.id
        st.session_state.sim_state = "execucao"
        st.session_state.sim_inicio_ts = datetime.utcnow().timestamp()
        st.session_state.sim_questao_idx = 0
        st.rerun()


# ============================================================================
# ESTADO 2: EXECUÇÃO
# ============================================================================
elif st.session_state.sim_state == "execucao":
    sim = get_simulado_completo(st.session_state.sim_id)
    questoes = sim["questoes"]
    total = len(questoes)

    if total == 0:
        st.error("Simulado sem questões. Descarte e inicie outro.")
        if st.button("Descartar"):
            descartar_simulado(st.session_state.sim_id)
            _reset_session()
            st.rerun()
        st.stop()

    idx = st.session_state.sim_questao_idx
    if idx >= total:
        idx = total - 1
    if idx < 0:
        idx = 0
    q = questoes[idx]

    # ------------------------------------------------------------------------
    # Sidebar — painel lateral de navegação
    # ------------------------------------------------------------------------
    with st.sidebar:
        st.divider()
        st.markdown("**Painel**")

        respondidas = sum(1 for x in questoes if x["resposta"])
        marcadas = sum(1 for x in questoes if x["marcada_revisar"])
        em_branco = total - respondidas

        st.caption(
            f"{respondidas}/{total} respondidas · {em_branco} em branco · "
            f"{marcadas} marcadas"
        )

        # Grid de botões pra navegação rápida
        cols_per_row = 5
        for row_start in range(0, total, cols_per_row):
            cols = st.columns(cols_per_row)
            for c, i in enumerate(range(row_start, min(row_start + cols_per_row, total))):
                qi = questoes[i]
                if qi["marcada_revisar"]:
                    label = f"⚑ {i+1}"
                elif qi["resposta"]:
                    label = f"✓ {i+1}"
                else:
                    label = f"{i+1}"
                btype = "primary" if i == idx else "secondary"
                if cols[c].button(label, key=f"nav_{i}", type=btype, use_container_width=True):
                    st.session_state.sim_questao_idx = i
                    st.rerun()

        st.divider()
        if st.button("Finalizar simulado", use_container_width=True):
            tempo_decorrido = int(datetime.utcnow().timestamp() - st.session_state.sim_inicio_ts)
            finalizar_simulado(st.session_state.sim_id, tempo_decorrido)
            st.session_state.sim_state = "resultado"
            st.rerun()

    # ------------------------------------------------------------------------
    # Header da questão
    # ------------------------------------------------------------------------
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(
            f"""
            <div style="font-family: 'Crimson Pro', serif; font-size: 1.8rem;
                        color: {COLOR_PRIMARY}; font-weight: 600;">
                Questão {idx + 1} <span style="color: {COLOR_MUTED}; font-size: 1.2rem;">
                de {total}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_h2:
        # Timer (se ativado)
        if sim["tempo_limite_segundos"]:
            elapsed = int(datetime.utcnow().timestamp() - st.session_state.sim_inicio_ts)
            restante = max(0, sim["tempo_limite_segundos"] - elapsed)
            mins, secs = divmod(restante, 60)
            timer_color = COLOR_ACCENT if restante < 300 else COLOR_PRIMARY
            st.markdown(
                f"""
                <div style="text-align: right; font-family: 'Crimson Pro', serif;
                            font-size: 1.5rem; color: {timer_color}; font-weight: 600;">
                    ⏱ {mins:02d}:{secs:02d}
                </div>
                """,
                unsafe_allow_html=True,
            )
            if restante == 0:
                st.warning("Tempo esgotado. Finalize o simulado.")

    st.write("")

    # ------------------------------------------------------------------------
    # Enunciado
    # ------------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="card">
            <div style="font-size: 1rem; line-height: 1.7; color: #1a1a1a;">
                {q['enunciado']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------------
    # Alternativas (radio)
    # ------------------------------------------------------------------------
    opcoes = [
        f"({letra}) {q['alternativas'][letra]}" for letra in "ABCDE"
    ]
    letras = list("ABCDE")

    # Estado: qual alternativa está selecionada
    resposta_atual = q["resposta"]
    default_idx = letras.index(resposta_atual) if resposta_atual in letras else None

    st.write("")
    selecionada = st.radio(
        "Sua resposta",
        options=range(5),
        format_func=lambda i: opcoes[i],
        index=default_idx,
        key=f"resp_{q['id']}",
    )

    # ------------------------------------------------------------------------
    # Bandeira "marcar pra revisar"
    # ------------------------------------------------------------------------
    revisar = st.checkbox(
        "⚑ Marcar para revisar depois",
        value=q["marcada_revisar"],
        key=f"rev_{q['id']}",
    )

    # ------------------------------------------------------------------------
    # Autosave: salva sempre que houve mudança
    # ------------------------------------------------------------------------
    nova_resposta = letras[selecionada] if selecionada is not None else None
    if nova_resposta != resposta_atual or revisar != q["marcada_revisar"]:
        responder_questao(
            simulado_id=st.session_state.sim_id,
            questao_id=q["id"],
            resposta_marcada=nova_resposta,
            marcada_revisar=revisar,
        )

    # ------------------------------------------------------------------------
    # Navegação
    # ------------------------------------------------------------------------
    st.write("")
    st.divider()

    col_a, col_b, col_c = st.columns([1, 2, 1])

    with col_a:
        if st.button("← Anterior", disabled=(idx == 0), use_container_width=True):
            st.session_state.sim_questao_idx = idx - 1
            st.rerun()

    with col_b:
        st.markdown(
            f"<div style='text-align: center; color: {COLOR_MUTED}; padding-top: 8px;'>"
            f"Questão {idx + 1} de {total}</div>",
            unsafe_allow_html=True,
        )

    with col_c:
        if idx == total - 1:
            # Última questão: vira botão de finalizar (não desabilita)
            if st.button(
                "Finalizar simulado",
                type="primary",
                use_container_width=True,
                key="btn_finalizar_inline",
            ):
                tempo_decorrido = int(
                    datetime.utcnow().timestamp() - st.session_state.sim_inicio_ts
                )
                finalizar_simulado(st.session_state.sim_id, tempo_decorrido)
                st.session_state.sim_state = "resultado"
                st.rerun()
        else:
            if st.button("Próxima →", use_container_width=True):
                st.session_state.sim_questao_idx = idx + 1
                st.rerun()


# ============================================================================
# ESTADO 3: RESULTADO
# ============================================================================
elif st.session_state.sim_state == "resultado":
    sim = get_simulado_completo(st.session_state.sim_id)
    n_acertos = sim["n_acertos"]
    total = sim["n_questoes"]
    pct = (n_acertos / total * 100) if total else 0

    st.title("Simulado concluído")
    subtitle("Resultado e revisão das questões")

    # Cartão grande de resultado
    cor_resultado = COLOR_FAIXA_OK if pct >= 70 else (COLOR_ACCENT if pct >= 50 else "#a8392b")
    st.markdown(
        f"""
        <div class="card" style="
            background: {cor_resultado};
            color: white;
            text-align: center;
            padding: 32px;
            border: none;
        ">
            <div style="font-family: 'Crimson Pro', serif; font-size: 1.1rem;
                        opacity: 0.9; text-transform: uppercase; letter-spacing: 0.06em;">
                Acertos
            </div>
            <div style="font-family: 'Crimson Pro', serif; font-size: 4rem;
                        font-weight: 700; line-height: 1; margin: 12px 0;">
                {n_acertos} <span style="font-size: 2rem; opacity: 0.7;">/ {total}</span>
            </div>
            <div style="font-family: 'Crimson Pro', serif; font-size: 1.5rem;">
                {pct:.0f}% de acerto
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown("### Revisão das questões")

    for i, q in enumerate(sim["questoes"], start=1):
        sua = q["resposta"] or "—"
        acertou = (q["resposta"] == q["gabarito"])
        ico = "✓" if acertou else ("✗" if q["resposta"] else "—")
        cor_ico = COLOR_FAIXA_OK if acertou else (COLOR_ACCENT if q["resposta"] else COLOR_MUTED)

        with st.expander(
            f"{ico} Questão {i} · sua resposta: {sua} · gabarito: {q['gabarito']}"
        ):
            st.markdown(q["enunciado"])
            st.write("")
            for letra in "ABCDE":
                if letra == q["gabarito"]:
                    bg = "#f0f5ed"
                    border = COLOR_FAIXA_OK
                    tag = "gabarito"
                elif letra == q["resposta"] and not acertou:
                    bg = "#fdf3f1"
                    border = COLOR_ACCENT
                    tag = "sua resposta"
                else:
                    bg = "white"
                    border = COLOR_BORDER
                    tag = ""

                st.markdown(
                    f"""
                    <div style="background: {bg}; border-left: 3px solid {border};
                                padding: 10px 14px; border-radius: 4px; margin: 4px 0;">
                        <strong>({letra})</strong> {q['alternativas'][letra]}
                        {f'<span style="float:right; color:{border}; font-size:0.85rem;">{tag}</span>' if tag else ''}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.write("")
            st.markdown(f"**Justificativa:** {q['justificativa']}")
            if q.get("fonte_descricao"):
                st.caption(f"Fonte: {q['fonte_descricao']}")
            if q.get("fonte_url"):
                st.markdown(f"[Abrir fonte]({q['fonte_url']})")

    st.write("")
    st.divider()

    if st.button("Iniciar novo simulado", type="primary", use_container_width=True):
        _reset_session()
        st.rerun()
