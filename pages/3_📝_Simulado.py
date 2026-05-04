"""
Página principal de simulado — modo "por disciplina" (Iter 1 do Step 6).

Estados controlados via st.session_state["sim_state"]:
- "selecao": tela inicial (escolhe disciplina + preset + timer)
- "execucao": rodando o simulado (1 questão por vez, painel lateral)
- "resultado": tela pós-finalização

Segurança:
- Toda chamada ao engine passa user.id pra validar ownership
- Conteúdo dinâmico (enunciado, alternativas, justificativa) é
  passado por html.escape() antes de injetar via unsafe_allow_html
"""
from __future__ import annotations

import html
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from db.database import db_session
from db.models import Disciplina
from modules.auth import exigir_login
from modules.config_loader import parametros_np
from modules.simulado_engine import (
    descartar_simulado,
    finalizar_simulado,
    get_simulado_completo,
    iniciar_simulado_por_disciplina,
    info_simulado,
    primeira_questao_nao_respondida,
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


def _esc(text: str | None) -> str:
    """HTML escape para conteúdo dinâmico injetado via unsafe_allow_html."""
    if text is None:
        return ""
    return html.escape(str(text))


def _url_seguro(url: str | None) -> str | None:
    """Valida que URL começa com http(s)://. Retorna None se for inválida ou maliciosa."""
    if not url:
        return None
    if not (url.startswith("http://") or url.startswith("https://")):
        return None
    return url


def _utcnow_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


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
    sim_id_andamento = simulado_em_andamento(user.id)
    if sim_id_andamento:
        sim_info = info_simulado(sim_id_andamento, user.id)
        # Garante timezone-aware pra .strftime funcionar consistentemente
        iniciado_em = sim_info["iniciado_em"]
        if iniciado_em.tzinfo is None:
            iniciado_em = iniciado_em.replace(tzinfo=timezone.utc)

        st.title("Você tem um simulado em andamento")
        subtitle(
            f"Iniciado em {iniciado_em.strftime('%d/%m/%Y %H:%M')} UTC · "
            f"{sim_info['n_questoes']} questões"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Retomar simulado", type="primary", use_container_width=True):
                st.session_state.sim_id = sim_id_andamento
                st.session_state.sim_state = "execucao"
                st.session_state.sim_inicio_ts = iniciado_em.timestamp()
                # #12: começa na primeira questão NÃO respondida (não em Q1 sempre)
                st.session_state.sim_questao_idx = primeira_questao_nao_respondida(
                    sim_id_andamento, user.id
                )
                st.rerun()
        with col2:
            if st.button("Descartar e começar outro", use_container_width=True):
                descartar_simulado(sim_id_andamento, user.id)
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

    with db_session() as session:
        disciplinas = session.query(Disciplina).order_by(Disciplina.ordem).all()
        # Snapshot dos dados — depois de fechar a session, objetos SQLAlchemy não funcionam
        disc_options = {d.nome: {"id": d.id, "nome": d.nome} for d in disciplinas}

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
                    <div style="font-weight: 500;">{_esc(disciplina['nome'])}</div>
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
        f"Ao iniciar, o sistema vai usar questões do banco primeiro e gerar "
        f"o restante via API se necessário (até {preset['questoes']} questões)."
    )

    if st.button("Iniciar simulado", type="primary", use_container_width=True):
        progress_bar = st.progress(0.0, text="Iniciando geração...")

        def on_progress(p):
            progress_bar.progress(
                p.pct,
                text=(
                    f"Gerando questões: {p.concluidas}/{p.total} prontas"
                    + (f" ({p.falhas} falharam)" if p.falhas else "")
                ),
            )

        try:
            simulado_id = iniciar_simulado_por_disciplina(
                usuario_id=user.id,
                disciplina_id=disciplina["id"],
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

        st.session_state.sim_id = simulado_id
        st.session_state.sim_state = "execucao"
        st.session_state.sim_inicio_ts = _utcnow_ts()
        st.session_state.sim_questao_idx = 0
        st.rerun()


# ============================================================================
# ESTADO 2: EXECUÇÃO
# ============================================================================
elif st.session_state.sim_state == "execucao":
    sim = get_simulado_completo(st.session_state.sim_id, user.id)
    questoes = sim["questoes"]
    total = len(questoes)

    if total == 0:
        st.error("Simulado sem questões. Descarte e inicie outro.")
        if st.button("Descartar"):
            descartar_simulado(st.session_state.sim_id, user.id)
            _reset_session()
            st.rerun()
        st.stop()

    # #9: bound check explícito (não confia em disabled=)
    idx = max(0, min(st.session_state.sim_questao_idx, total - 1))
    st.session_state.sim_questao_idx = idx
    q = questoes[idx]

    # #11: flag pra prevenir double-finalize
    if "sim_finalizando" not in st.session_state:
        st.session_state.sim_finalizando = False

    def _finalizar_e_navegar():
        """Idempotente: finaliza e vai pra tela de resultado."""
        if st.session_state.sim_finalizando:
            return
        st.session_state.sim_finalizando = True
        tempo_decorrido = int(_utcnow_ts() - st.session_state.sim_inicio_ts)
        finalizar_simulado(st.session_state.sim_id, user.id, tempo_decorrido)
        st.session_state.sim_state = "resultado"
        st.session_state.sim_finalizando = False
        st.rerun()

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
        if st.button("Finalizar simulado", use_container_width=True, key="btn_finalizar_sidebar"):
            _finalizar_e_navegar()

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
        if sim["tempo_limite_segundos"]:
            elapsed = int(_utcnow_ts() - st.session_state.sim_inicio_ts)
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
    # Enunciado (com escape de HTML)
    # ------------------------------------------------------------------------
    st.markdown(
        f"""
        <div class="card">
            <div style="font-size: 1rem; line-height: 1.7; color: #1a1a1a;
                        white-space: pre-wrap;">{_esc(q['enunciado'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------------
    # Alternativas (radio) — sem escape porque vai como string Python para st.radio
    # ------------------------------------------------------------------------
    opcoes = [
        f"({letra}) {q['alternativas'][letra]}" for letra in "ABCDE"
    ]
    letras = list("ABCDE")

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

    revisar = st.checkbox(
        "⚑ Marcar para revisar depois",
        value=q["marcada_revisar"],
        key=f"rev_{q['id']}",
    )

    # Autosave: salva sempre que houve mudança
    nova_resposta = letras[selecionada] if selecionada is not None else None
    if nova_resposta != resposta_atual or revisar != q["marcada_revisar"]:
        responder_questao(
            simulado_id=st.session_state.sim_id,
            usuario_id=user.id,
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
        # #9: bound check explícito (não só disabled=)
        if idx > 0 and st.button("← Anterior", use_container_width=True):
            st.session_state.sim_questao_idx = idx - 1
            st.rerun()
        elif idx == 0:
            st.button("← Anterior", disabled=True, use_container_width=True)

    with col_b:
        st.markdown(
            f"<div style='text-align: center; color: {COLOR_MUTED}; padding-top: 8px;'>"
            f"Questão {idx + 1} de {total}</div>",
            unsafe_allow_html=True,
        )

    with col_c:
        if idx == total - 1:
            if st.button(
                "Finalizar simulado",
                type="primary",
                use_container_width=True,
                key="btn_finalizar_inline",
            ):
                _finalizar_e_navegar()
        else:
            if st.button("Próxima →", use_container_width=True):
                st.session_state.sim_questao_idx = idx + 1
                st.rerun()


# ============================================================================
# ESTADO 3: RESULTADO
# ============================================================================
elif st.session_state.sim_state == "resultado":
    sim = get_simulado_completo(st.session_state.sim_id, user.id)
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

        with st.expander(
            f"{ico} Questão {i} · sua resposta: {sua} · gabarito: {q['gabarito']}"
        ):
            # Enunciado escapado
            st.markdown(
                f'<div style="white-space: pre-wrap;">{_esc(q["enunciado"])}</div>',
                unsafe_allow_html=True,
            )
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
                        <strong>({letra})</strong> {_esc(q['alternativas'][letra])}
                        {f'<span style="float:right; color:{border}; font-size:0.85rem;">{tag}</span>' if tag else ''}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.write("")
            # Justificativa via st.markdown puro (Markdown nativo, sem unsafe_allow_html)
            st.markdown(f"**Justificativa:** {q['justificativa']}")
            if q.get("fonte_descricao"):
                st.caption(f"Fonte: {q['fonte_descricao']}")
            url_safe = _url_seguro(q.get("fonte_url"))
            if url_safe:
                st.markdown(f"[Abrir fonte]({url_safe})")

    st.write("")
    st.divider()

    if st.button("Iniciar novo simulado", type="primary", use_container_width=True):
        _reset_session()
        st.rerun()
