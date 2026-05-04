"""
Página admin — visão do banco de questões pré-geradas.

Mostra:
- Total de questões no banco
- Distribuição por disciplina e sub-tópico
- Cobertura (% de sub-tópicos com pelo menos 1 questão)

Útil pra Romel saber onde precisa gerar mais questões manualmente.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from collections import defaultdict

import streamlit as st
from sqlalchemy import func

from db.database import db_session
from db.models import BancoQuestao, BlocoEdital, Disciplina, PerfilUsuario, SubTopico
from modules.auth import exigir_login
from modules.theme import COLOR_BORDER, COLOR_MUTED, COLOR_PRIMARY, apply_theme, subtitle
from modules.version import get_build_info


st.set_page_config(
    page_title="Banco de Questões — Riri Auditora",
    page_icon="📚",
    layout="wide",
)

apply_theme()
user = exigir_login()

if user.perfil != PerfilUsuario.ADMIN:
    st.error("Acesso restrito ao admin.")
    st.stop()

with st.sidebar:
    build = get_build_info()
    deploy_str = (
        build.deploy_time.strftime("%d/%m %H:%M UTC")
        if build.deploy_time else "?"
    )
    st.caption(f"Build `{build.short_sha}` · {build.ref_name} · {deploy_str}")


st.title("Banco de questões")
subtitle("Pool de questões pré-geradas — usado antes da API em cada simulado")


with db_session() as session:
    total = session.query(BancoQuestao).count()
    disciplinas = session.query(Disciplina).order_by(Disciplina.ordem).all()
    sub_topicos_total = session.query(SubTopico).count()

    # #4: Aggregação SQL — uma query em vez de N+1
    counts = (
        session.query(BancoQuestao.sub_topico_id, func.count(BancoQuestao.id))
        .group_by(BancoQuestao.sub_topico_id)
        .all()
    )
    contagem_por_sub: dict[int, int] = defaultdict(int, dict(counts))

    sub_topicos_cobertos = sum(1 for n in contagem_por_sub.values() if n > 0)
    pct_cobertura = (sub_topicos_cobertos / sub_topicos_total * 100) if sub_topicos_total else 0

    # Métricas globais
    col1, col2, col3 = st.columns(3)
    col1.metric("Total no banco", total)
    col2.metric("Sub-tópicos cobertos", f"{sub_topicos_cobertos} de {sub_topicos_total}")
    col3.metric("Cobertura", f"{pct_cobertura:.0f}%")

    if total == 0:
        st.write("")
        st.info(
            "Banco vazio. Para popular: adicione questões em "
            "`app/seed_data/questoes_iniciais.json` e rode "
            "`python -m db.seed_banco_questoes` localmente, ou peça ao Claude (no chat) "
            "pra gerar mais lotes."
        )

    st.write("")
    st.markdown("### Distribuição por disciplina")

    for d in disciplinas:
        sub_topicos_da_disc = (
            session.query(SubTopico)
            .filter_by(disciplina_id=d.id)
            .order_by(SubTopico.ordem)
            .all()
        )
        n_total_disc = sum(contagem_por_sub.get(st_.id, 0) for st_ in sub_topicos_da_disc)
        n_cobertos = sum(1 for st_ in sub_topicos_da_disc if contagem_por_sub.get(st_.id, 0) > 0)

        bloco_label = "Gerais" if d.bloco == BlocoEdital.GERAIS else "Específicos"

        with st.expander(
            f"**{d.nome}** ({bloco_label}, peso {d.peso}×) — "
            f"{n_total_disc} questões · "
            f"{n_cobertos}/{len(sub_topicos_da_disc)} sub-tópicos cobertos"
        ):
            for st_ in sub_topicos_da_disc:
                count = contagem_por_sub.get(st_.id, 0)
                if count == 0:
                    icon = "○"
                    color = COLOR_MUTED
                elif count < 3:
                    icon = "◐"
                    color = "#a17e2a"
                else:
                    icon = "●"
                    color = "#3d6b3d"
                # #3: escape no nome do sub-tópico (vem do banco)
                import html as _html  # local pra evitar import-as-shadow no top
                nome_safe = _html.escape(st_.nome)
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center;
                                padding: 4px 8px; margin: 2px 0;
                                border-bottom: 1px solid {COLOR_BORDER};">
                        <span style="color: {color}; font-size: 1.2rem;
                                     margin-right: 12px;">{icon}</span>
                        <div style="flex: 1; font-size: 0.9rem;">{nome_safe}</div>
                        <div style="color: {COLOR_MUTED}; font-size: 0.85rem;">
                            {count} questão{'ões' if count != 1 else ''}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ============================================================================
# Como adicionar mais questões
# ============================================================================
st.write("")
st.divider()
with st.expander("Como adicionar mais questões ao banco"):
    st.markdown(
        """
        **Fluxo recomendado** (sem custo de API):

        1. **Abra uma conversa no Claude.ai** (sua conta Pro)
        2. Peça pra gerar N questões estilo FCC sobre disciplina/sub-tópico específico
        3. Peça que retorne **no formato JSON** do arquivo `seed_data/questoes_iniciais.json`
        4. Cole as questões no JSON
        5. Rode localmente: `python -m db.seed_banco_questoes`
        6. As novas questões aparecerão aqui

        **Atalho:** se você está no Claude Code conversando comigo, posso gerar
        e escrever direto no JSON. Basta dizer:
        > "Gere 10 questões de Direito Tributário e adicione ao banco"

        **Tip:** o script é idempotente — duplicatas (detectadas pelo enunciado)
        são ignoradas. Você pode rodar quantas vezes quiser.
        """
    )
