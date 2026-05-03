"""
Importa questões pré-geradas (via Claude.ai, sem custo de API) para BancoQuestao.

Lê de: app/seed_data/questoes_iniciais.json
Formato: ver app/seed_data/README_FORMATO.md

Uso:
    python -m db.seed_banco_questoes              # importa tudo
    python -m db.seed_banco_questoes --reset      # apaga banco antes
    python -m db.seed_banco_questoes --arquivo X  # importa arquivo específico

Idempotente: detecta duplicatas pelo enunciado e ignora (não recria).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Permite rodar como módulo OU como script direto
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.database import get_session, init_db
from db.models import BancoQuestao, Disciplina, FonteOrigem, SubTopico


def _resolve_sub_topico(session, disciplina_nome: str, sub_topico_nome: str) -> SubTopico | None:
    """Busca sub-tópico pelo nome (case-insensitive, normalizando whitespace)."""
    sub = (
        session.query(SubTopico)
        .join(Disciplina)
        .filter(
            Disciplina.nome == disciplina_nome,
            SubTopico.nome == sub_topico_nome,
        )
        .first()
    )
    if sub:
        return sub

    # Fallback: case-insensitive partial match
    sub = (
        session.query(SubTopico)
        .join(Disciplina)
        .filter(
            Disciplina.nome.ilike(f"%{disciplina_nome}%"),
            SubTopico.nome.ilike(f"%{sub_topico_nome}%"),
        )
        .first()
    )
    return sub


def importar(arquivo: Path, reset: bool = False) -> dict:
    """
    Importa questões do arquivo JSON. Retorna dict com contagens.
    """
    init_db()

    with open(arquivo, encoding="utf-8") as f:
        data = json.load(f)

    questoes_input = data.get("questoes", [])
    if not questoes_input:
        return {"total": 0, "importadas": 0, "duplicadas": 0, "sub_topico_nao_encontrado": 0}

    session = get_session()
    try:
        if reset:
            n = session.query(BancoQuestao).delete()
            print(f"Reset: {n} questões removidas do banco.")
            session.commit()

        importadas = 0
        duplicadas = 0
        nao_encontradas = []

        for q in questoes_input:
            sub = _resolve_sub_topico(session, q["disciplina"], q["sub_topico"])
            if not sub:
                nao_encontradas.append(f"{q['disciplina']} > {q['sub_topico']}")
                continue

            # Detecta duplicata por enunciado (normalizado)
            enunciado_norm = " ".join(q["enunciado"].split())
            existing = (
                session.query(BancoQuestao)
                .filter_by(sub_topico_id=sub.id)
                .filter(BancoQuestao.enunciado.like(f"%{enunciado_norm[:80]}%"))
                .first()
            )
            if existing:
                duplicadas += 1
                continue

            fonte_origem = None
            if q.get("fonte_url"):
                if "doutrina" in (q.get("fonte_origem") or "").lower():
                    fonte_origem = FonteOrigem.DOUTRINA
                elif "local" in (q.get("fonte_origem") or "").lower():
                    fonte_origem = FonteOrigem.LOCAL
                else:
                    fonte_origem = FonteOrigem.WEB

            session.add(BancoQuestao(
                sub_topico_id=sub.id,
                enunciado=q["enunciado"],
                alternativa_a=q["alternativas"]["A"],
                alternativa_b=q["alternativas"]["B"],
                alternativa_c=q["alternativas"]["C"],
                alternativa_d=q["alternativas"]["D"],
                alternativa_e=q["alternativas"]["E"],
                gabarito=q["gabarito"],
                justificativa=q["justificativa"],
                fonte_descricao=q.get("fonte_descricao"),
                fonte_url=q.get("fonte_url"),
                fonte_origem=fonte_origem,
                alerta_revisao=q.get("alerta_revisao", False),
                origem=q.get("origem", "manual"),
            ))
            importadas += 1

        session.commit()

        return {
            "total": len(questoes_input),
            "importadas": importadas,
            "duplicadas": duplicadas,
            "sub_topico_nao_encontrado": len(nao_encontradas),
            "nao_encontradas_lista": nao_encontradas,
        }
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Importa questões pré-geradas para BancoQuestao.")
    parser.add_argument(
        "--arquivo",
        type=Path,
        default=Path(__file__).parent.parent / "seed_data" / "questoes_iniciais.json",
    )
    parser.add_argument("--reset", action="store_true", help="Apaga o banco antes de importar.")
    args = parser.parse_args()

    if not args.arquivo.exists():
        print(f"Arquivo não encontrado: {args.arquivo}")
        sys.exit(1)

    print(f"Importando de: {args.arquivo}")
    result = importar(args.arquivo, reset=args.reset)

    print()
    print("=" * 60)
    print(f"Total no JSON:           {result['total']}")
    print(f"Importadas:              {result['importadas']}")
    print(f"Duplicadas (puladas):    {result['duplicadas']}")
    print(f"Sub-tópico não casou:    {result['sub_topico_nao_encontrado']}")
    if result.get("nao_encontradas_lista"):
        print()
        print("Sub-tópicos não casados (revise nomes):")
        for nome in result["nao_encontradas_lista"]:
            print(f"  - {nome}")
    print("=" * 60)


if __name__ == "__main__":
    main()
