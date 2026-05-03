"""
Teste do motor de cálculo da Nota Padronizada.

Cobre cenários conhecidos onde o resultado esperado é matematicamente óbvio.
Não usa pytest pra evitar dep extra — só asserts.

Uso:
    cd app
    python scripts/test_np.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Força UTF-8 no stdout (Windows console)
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.np_calculator import (  # noqa: E402
    calcular_np,
    calcular_score,
    nivel_proficiencia,
)


def assert_close(actual: float, expected: float, tol: float = 0.01, label: str = ""):
    if abs(actual - expected) > tol:
        raise AssertionError(
            f"{label}: esperado {expected}, recebido {actual} (diff {abs(actual-expected):.4f})"
        )
    print(f"  OK {label}: {actual:.2f}")


def test_formula_basica():
    """NP de candidato exatamente na média deve ser 50."""
    print("\n[Teste 1] Fórmula básica: candidato = média do grupo → NP=50")
    assert_close(calcular_np(40, 40, 10), 50.0, label="acertos=média")
    assert_close(calcular_np(50, 40, 10), 60.0, label="1 DP acima da média")
    assert_close(calcular_np(30, 40, 10), 40.0, label="1 DP abaixo da média")
    assert_close(calcular_np(60, 40, 10), 70.0, label="2 DP acima")


def test_dp_zero():
    """Edital item 9.5(b): se DP=0, usa 1 como divisor."""
    print("\n[Teste 2] DP=0 (edital prevê fallback para 1)")
    # Com DP efetivo=1: ((50-40)/1)*10+50 = 150
    assert_close(calcular_np(50, 40, 0), 150.0, label="DP=0, acertos>média")


def test_candidato_mediano():
    """Mediano (40 G, 38 E) deve dar score = 150 (corte exato)."""
    print("\n[Teste 3] Candidato mediano → score = 150 (corte)")
    r = calcular_score(acertos_gerais=40, acertos_especificos=38)
    assert_close(r.np_gerais, 50.0, label="NP_gerais")
    assert_close(r.np_especificos, 50.0, label="NP_especificos")
    assert_close(r.score_final, 150.0, label="score (50*1 + 50*2)")
    assert r.faixa.nome == "Chance média", f"Faixa esperada 'Chance média', recebida '{r.faixa.nome}'"
    print(f"  OK faixa: {r.faixa.nome}")


def test_candidato_bom():
    """Bom (50 G, 55 E) deve estar na faixa alta ou Vai passar."""
    print("\n[Teste 4] Candidato bom (50 G, 55 E)")
    r = calcular_score(acertos_gerais=50, acertos_especificos=55)
    # NP_g = ((50-40)/10)*10+50 = 60
    # NP_e = ((55-38)/12)*10+50 = 64.17
    # Score = 60 + 128.33 = 188.33
    assert_close(r.np_gerais, 60.0, label="NP_gerais")
    assert_close(r.np_especificos, 64.17, label="NP_especificos")
    assert_close(r.score_final, 188.33, label="score")
    assert r.faixa.nome == "Vai passar!", f"Esperada 'Vai passar!', recebida '{r.faixa.nome}'"
    assert r.passou_corte, "Deveria passar do corte"
    print(f"  OK faixa: {r.faixa.nome}")


def test_candidato_fraco():
    """Fraco (25 G, 20 E) deve estar em Pouca chance."""
    print("\n[Teste 5] Candidato fraco (25 G, 20 E)")
    r = calcular_score(acertos_gerais=25, acertos_especificos=20)
    assert r.faixa.nome == "Pouca chance", f"Esperada 'Pouca chance', recebida '{r.faixa.nome}'"
    assert not r.passou_corte
    print(f"  OK score={r.score_final:.2f}, faixa={r.faixa.nome}")


def test_niveis_proficiencia():
    """Os 4 níveis devem mapear corretamente."""
    print("\n[Teste 6] Níveis de proficiência por % acerto")
    casos = [
        (0, "Crítico"),
        (49, "Crítico"),
        (50, "Em desenvolvimento"),
        (69, "Em desenvolvimento"),
        (70, "Satisfatório"),
        (84, "Satisfatório"),
        (85, "Dominado"),
        (100, "Dominado"),
    ]
    for pct, esperado in casos:
        n = nivel_proficiencia(pct)
        assert n.nome == esperado, f"{pct}% → esperado '{esperado}', recebido '{n.nome}'"
        print(f"  OK {pct}% → {n.nome}")


def main():
    print("=" * 70)
    print("TESTE DO MOTOR DE NOTA PADRONIZADA")
    print("=" * 70)

    test_formula_basica()
    test_dp_zero()
    test_candidato_mediano()
    test_candidato_bom()
    test_candidato_fraco()
    test_niveis_proficiencia()

    print()
    print("=" * 70)
    print("TODOS OS TESTES PASSARAM ✓")
    print("=" * 70)


if __name__ == "__main__":
    main()
