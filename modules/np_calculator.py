"""
Motor de cálculo da Nota Padronizada (NP) — Sefaz CE 2026.

Fórmula oficial do edital (item 9.5):
    NP = [(Acertos - Média do grupo) / Desvio Padrão do grupo] × 10 + 50

Score final = NP_Gerais × peso_gerais (1) + NP_Específicos × peso_especificos (2)

Corte de habilitação: ≥ 150 pontos (= candidato mediano com NP=50 em ambos os blocos).

Parâmetros (médias e desvios padrão estimados) ficam em config/parametros_np.yml.
São premissas baseadas em concursos FCC Sefaz anteriores e devem ser refinados
quando o histórico real surgir.
"""
from __future__ import annotations

from dataclasses import dataclass

from modules.config_loader import parametros_np


# ============================================================================
# Estruturas de retorno
# ============================================================================
@dataclass(frozen=True)
class FaixaChance:
    nome: str
    cor: str  # hex
    emoji: str
    mensagem: str
    score_min: int
    score_max: int


@dataclass(frozen=True)
class NivelProficiencia:
    nome: str
    cor: str  # hex
    pct_min: int
    pct_max: int


@dataclass(frozen=True)
class ResultadoNP:
    np_gerais: float
    np_especificos: float
    score_final: float
    faixa: FaixaChance

    acertos_gerais: int
    acertos_especificos: int

    @property
    def passou_corte(self) -> bool:
        return self.score_final >= 150


# ============================================================================
# Fórmula básica
# ============================================================================
def calcular_np(acertos: int, media_grupo: float, dp_grupo: float) -> float:
    """
    Aplica a fórmula da Nota Padronizada.

    Conforme edital item 9.5(b): se o desvio padrão do grupo for zero,
    usa-se valor 1 para o cálculo (evita divisão por zero).
    """
    dp_efetivo = dp_grupo if dp_grupo > 0 else 1
    return ((acertos - media_grupo) / dp_efetivo) * 10 + 50


# ============================================================================
# Score final + classificação
# ============================================================================
def calcular_score(acertos_gerais: int, acertos_especificos: int) -> ResultadoNP:
    """
    Calcula NP de cada bloco, score final ponderado e a faixa de chance.

    Args:
        acertos_gerais: número de acertos em Conhecimentos Gerais (0-80)
        acertos_especificos: número de acertos em Conhecimentos Específicos (0-80)

    Returns:
        ResultadoNP com NP por bloco, score final, faixa e flag de aprovação.
    """
    cfg = parametros_np()

    g = cfg["conhecimentos_gerais"]
    e = cfg["conhecimentos_especificos"]
    peso_g = cfg["peso_gerais"]
    peso_e = cfg["peso_especificos"]

    np_g = calcular_np(acertos_gerais, g["media_acertos_grupo"], g["desvio_padrao_grupo"])
    np_e = calcular_np(acertos_especificos, e["media_acertos_grupo"], e["desvio_padrao_grupo"])
    score = np_g * peso_g + np_e * peso_e

    return ResultadoNP(
        np_gerais=np_g,
        np_especificos=np_e,
        score_final=score,
        faixa=classificar_faixa(score),
        acertos_gerais=acertos_gerais,
        acertos_especificos=acertos_especificos,
    )


def classificar_faixa(score: float) -> FaixaChance:
    """Mapeia score final na faixa de chance correspondente (4 bandas)."""
    cfg = parametros_np()
    for f in cfg["faixas"]:
        if f["score_min"] <= score <= f["score_max"]:
            return FaixaChance(
                nome=f["nome"],
                cor=f["cor"],
                emoji=f["emoji"],
                mensagem=f["mensagem"],
                score_min=f["score_min"],
                score_max=f["score_max"],
            )
    # Fallback: score fora de qualquer faixa (não deveria acontecer)
    raise ValueError(f"Score {score} não se encaixa em nenhuma faixa configurada.")


# ============================================================================
# Proficiência por sub-tópico (% acerto → nível)
# ============================================================================
def nivel_proficiencia(pct_acerto: float) -> NivelProficiencia:
    """
    Retorna o nível de proficiência baseado no % de acerto (0-100).
    Crítico / Em desenvolvimento / Satisfatório / Dominado.
    """
    cfg = parametros_np()
    pct = max(0, min(100, pct_acerto))  # clamp 0-100
    for n in cfg["niveis_proficiencia"]:
        if n["pct_min"] <= pct <= n["pct_max"]:
            return NivelProficiencia(
                nome=n["nome"],
                cor=n["cor"],
                pct_min=n["pct_min"],
                pct_max=n["pct_max"],
            )
    raise ValueError(f"% acerto {pct} não se encaixa em nenhum nível.")
