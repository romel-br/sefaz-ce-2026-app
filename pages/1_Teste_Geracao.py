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


st.set_page_config(
    page_title="Teste de Geração — Sefaz CE 2026",
    page_icon="🧪",
    layout="wide",
)


# ============================================================================
# Auth — só admin acessa
# ============================================================================
user = exigir_login()
if user.perfil != PerfilUsuario.ADMIN:
    st.error("⛔ Acesso restrito ao admin.")
    st.stop()


# ============================================================================
# UI
# ============================================================================
st.title("🧪 Teste de Geração de Questões")
st.caption("Calibração da qualidade — gera questões via Claude API sem persistir no banco.")

session = get_session()
try:
    disciplinas = (
        session.query(Disciplina).order_by(Disciplina.ordem).all()
    )

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
        st.metric("Bloco", bloco_label)
        st.metric("Peso na prova", f"{disciplina.peso}x")
        st.metric("Questões na prova real", disciplina.n_questoes_prova)

        quantidade = st.number_input(
            "Quantas questões gerar",
            min_value=1, max_value=5, value=1,
            help="Recomendado 1-2 para testes rápidos. 5 leva ~2 min.",
        )

    if st.button("🚀 Gerar questões", type="primary", use_container_width=True):
        with st.spinner(
            f"Gerando {quantidade} questão(ões)... isso leva 30-90s "
            "(thinking + web_search + structured output)"
        ):
            try:
                result = gerar_questoes(
                    disciplina=disc_nome,
                    sub_topico=sub_nome,
                    bloco=bloco_label,
                    quantidade=int(quantidade),
                )
            except Exception as e:
                st.error(f"❌ Erro na geração: {type(e).__name__}: {e}")
                st.exception(e)
                st.stop()

        # ====================================================================
        # Renderização das questões
        # ====================================================================
        st.success(f"✅ {len(result['questoes'])} questão(ões) gerada(s) com sucesso.")

        # Métricas de uso/custo
        usage = result["usage"]
        cache_read = usage.get("cache_read_input_tokens", 0)
        cache_write = usage.get("cache_creation_input_tokens", 0)

        with st.expander("📊 Métricas da chamada", expanded=False):
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            mcol1.metric("Input fresh", usage["input_tokens"])
            mcol2.metric("Cache write", cache_write)
            mcol3.metric("Cache read", cache_read, help="Lido do cache (~10% do custo)")
            mcol4.metric("Output", usage["output_tokens"])

            # Custo estimado (claude-opus-4-7: $5/M input, $25/M output)
            cost_input = usage["input_tokens"] * 5 / 1_000_000
            cost_cache_w = cache_write * 5 * 1.25 / 1_000_000
            cost_cache_r = cache_read * 5 * 0.1 / 1_000_000
            cost_output = usage["output_tokens"] * 25 / 1_000_000
            total = cost_input + cost_cache_w + cost_cache_r + cost_output
            st.caption(f"💰 Custo desta chamada: ~US$ {total:.4f} | Modelo: {result['model']}")

        # Render cada questão
        for i, q in enumerate(result["questoes"], start=1):
            st.divider()
            st.subheader(f"Questão {i}")

            st.markdown(q["enunciado"])
            st.write("")

            for letra in "ABCDE":
                if letra == q["gabarito"]:
                    st.success(f"**({letra})** {q['alternativas'][letra]}  ✅")
                else:
                    st.markdown(f"**({letra})** {q['alternativas'][letra]}")

            with st.expander(f"📖 Justificativa e fonte da Questão {i}"):
                st.markdown(f"**Gabarito:** {q['gabarito']}")
                st.markdown(f"**Justificativa:**\n\n{q['justificativa']}")
                st.markdown(f"**Fonte:** {q['fonte_descricao']}")
                if q.get("fonte_url"):
                    st.markdown(f"**URL:** [{q['fonte_url']}]({q['fonte_url']})")
                if q.get("alerta_revisao"):
                    st.warning("⚠️ Esta questão precisa de revisão manual (fonte incerta).")

finally:
    session.close()
