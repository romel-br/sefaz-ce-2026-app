"""
Teste local do motor de geração de questões.

Gera 1 questão para um sub-tópico simples e imprime o resultado.
Não persiste no banco — só valida que a integração com Claude API funciona.

Uso:
    cd app
    python scripts/test_generation.py

    # Ou para outro sub-tópico:
    python scripts/test_generation.py --disciplina "Direito Constitucional, Administrativo, Civil e Penal" \
        --sub-topico "Direitos e garantias fundamentais" \
        --bloco "Conhecimentos Gerais"
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Força UTF-8 no stdout (Windows console default cp1252 quebra com unicode)
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Permite rodar como script (sem instalar como pacote)
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.question_generator import gerar_questoes  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)


def main():
    parser = argparse.ArgumentParser(description="Testa geração de 1 questão.")
    parser.add_argument(
        "--disciplina", default="Direito Tributário",
        help="Nome da disciplina (default: Direito Tributário)"
    )
    parser.add_argument(
        "--sub-topico", default="Limitações constitucionais do poder de tributar",
        help="Sub-tópico específico"
    )
    parser.add_argument(
        "--bloco", default="Conhecimentos Específicos",
        choices=["Conhecimentos Gerais", "Conhecimentos Específicos"],
    )
    parser.add_argument("--quantidade", type=int, default=1)
    args = parser.parse_args()

    print("=" * 80)
    print(f"GERANDO {args.quantidade} questão(ões)")
    print(f"Disciplina: {args.disciplina}")
    print(f"Sub-tópico: {args.sub_topico}")
    print(f"Bloco:      {args.bloco}")
    print("=" * 80)
    print("(isso pode levar 30-90 segundos com web_search + thinking)")
    print()

    result = gerar_questoes(
        disciplina=args.disciplina,
        sub_topico=args.sub_topico,
        bloco=args.bloco,
        quantidade=args.quantidade,
    )

    print()
    print("=" * 80)
    print("METADADOS")
    print("=" * 80)
    print(f"Model:       {result['model']}")
    print(f"Stop reason: {result['stop_reason']}")
    print(f"Usage:       {json.dumps(result['usage'], indent=2)}")
    print()

    for i, q in enumerate(result["questoes"], start=1):
        print("=" * 80)
        print(f"QUESTÃO {i}")
        print("=" * 80)
        print(f"\n{q['enunciado']}\n")
        for letra in "ABCDE":
            marca = "[OK]" if letra == q["gabarito"] else "    "
            print(f"  {marca} ({letra}) {q['alternativas'][letra]}")
        print(f"\nGabarito: {q['gabarito']}")
        print(f"\nJustificativa:\n{q['justificativa']}")
        print(f"\nFonte: {q['fonte_descricao']}")
        if q.get("fonte_url"):
            print(f"URL:   {q['fonte_url']}")
        if q.get("alerta_revisao"):
            print("\n⚠️  ALERTA: esta questão precisa de revisão manual (fonte incerta)")
        print()


if __name__ == "__main__":
    main()
