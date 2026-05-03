"""
Motor de simulados — orquestra criação, execução e finalização.

Responsabilidades:
- Amostrar sub-tópicos para um simulado
- Gerar questões em paralelo (ThreadPool)
- Persistir Simulado/Questao/Resposta no banco
- Atualizar respostas (autosave)
- Calcular acertos e finalizar

Não faz cálculo de NP nem gera material — isso é responsabilidade
de outros módulos (np_calculator, futuramente material_generator).
"""
from __future__ import annotations

import logging
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from sqlalchemy import func

from db.database import get_session
from db.models import (
    BancoQuestao,
    BlocoEdital,
    Disciplina,
    FonteOrigem,
    ModoSimulado,
    Questao,
    Resposta,
    Simulado,
    StatusSimulado,
    SubTopico,
    Usuario,
)
from modules.question_generator import gerar_questoes

logger = logging.getLogger(__name__)


# ============================================================================
# Estruturas auxiliares
# ============================================================================
@dataclass(frozen=True)
class ProgressoGeracao:
    """Status da geração de questões em andamento."""
    total: int
    concluidas: int
    falhas: int

    @property
    def pct(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.concluidas + self.falhas) / self.total


# ============================================================================
# Amostragem de sub-tópicos
# ============================================================================
def _amostrar_sub_topicos(
    session: Session,
    disciplina_id: int,
    n_questoes: int,
) -> list[SubTopico]:
    """
    Sorteia N sub-tópicos da disciplina (com reposição se N > total).
    Retorna a lista (pode conter repetições — a geração lida com isso).
    """
    sub_topicos = (
        session.query(SubTopico)
        .filter_by(disciplina_id=disciplina_id)
        .all()
    )
    if not sub_topicos:
        raise ValueError(f"Disciplina {disciplina_id} não tem sub-tópicos.")

    # Se há sub-tópicos suficientes, amostra sem reposição
    if len(sub_topicos) >= n_questoes:
        return random.sample(sub_topicos, n_questoes)

    # Senão, amostragem com reposição
    return [random.choice(sub_topicos) for _ in range(n_questoes)]


# ============================================================================
# Geração paralela de questões
# ============================================================================
def _gerar_uma_questao(sub_topico: SubTopico, bloco_label: str, disciplina_nome: str) -> dict | None:
    """
    Gera 1 questão para um sub-tópico. Retorna dict da questão ou None se falhou.
    Usado pelo ThreadPool — encapsula erros pra não derrubar o lote inteiro.
    """
    try:
        result = gerar_questoes(
            disciplina=disciplina_nome,
            sub_topico=sub_topico.nome,
            bloco=bloco_label,
            quantidade=1,
        )
        if not result.get("questoes"):
            return None
        questao_data = result["questoes"][0]
        # Anexa o sub_topico_id para persistência
        questao_data["_sub_topico_id"] = sub_topico.id
        return questao_data
    except Exception as e:
        logger.exception("Falha gerando questão para sub-tópico %s: %s", sub_topico.nome, e)
        return None


def _gerar_questoes_em_paralelo(
    sub_topicos: list[SubTopico],
    disciplina_nome: str,
    bloco_label: str,
    progresso_callback=None,
    max_workers: int = 5,
) -> list[dict]:
    """
    Gera 1 questão por sub-tópico em paralelo (ThreadPool).
    Chama progresso_callback(ProgressoGeracao) a cada conclusão.
    Retorna lista de questoes (dicts) — descarta as que falharam.
    """
    total = len(sub_topicos)
    questoes_geradas: list[dict] = []
    falhas = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_gerar_uma_questao, st, bloco_label, disciplina_nome): st
            for st in sub_topicos
        }
        for future in as_completed(futures):
            result = future.result()
            if result is None:
                falhas += 1
            else:
                questoes_geradas.append(result)
            if progresso_callback:
                progresso_callback(
                    ProgressoGeracao(
                        total=total,
                        concluidas=len(questoes_geradas),
                        falhas=falhas,
                    )
                )

    return questoes_geradas


# ============================================================================
# Criação de simulado
# ============================================================================
def _puxar_do_banco(
    session: Session,
    disciplina_id: int,
    n_questoes: int,
) -> list[BancoQuestao]:
    """
    Sorteia até N questões do BancoQuestao filtrando por disciplina.
    Retorna até N (pode retornar menos se banco não tiver suficientes).
    """
    questoes_disponiveis = (
        session.query(BancoQuestao)
        .join(SubTopico)
        .filter(SubTopico.disciplina_id == disciplina_id)
        .order_by(func.random())  # PostgreSQL random() — em SQLite seria func.random() também
        .limit(n_questoes)
        .all()
    )
    return questoes_disponiveis


def iniciar_simulado_por_disciplina(
    usuario_id: int,
    disciplina_id: int,
    n_questoes: int,
    com_timer: bool,
    tempo_limite_segundos: int | None = None,
    progresso_callback=None,
    permitir_api_fallback: bool = True,
) -> Simulado:
    """
    Cria um simulado por disciplina:
    1. Busca questões no BancoQuestao primeiro (sem custo de API).
    2. Se faltarem, gera o restante via API (parallel ThreadPool).
    3. Persiste tudo como Questao vinculada ao Simulado.

    Args:
        usuario_id: ID do usuário (Ariane)
        disciplina_id: ID da disciplina escolhida
        n_questoes: 10/20/40 (presets) ou custom
        com_timer: se True, ativa timer (tempo_limite_segundos obrigatório)
        tempo_limite_segundos: se com_timer=True
        progresso_callback: callback(ProgressoGeracao) durante geração via API
        permitir_api_fallback: se False, falha se banco não tiver questões suficientes
                              (útil pra modo "100% offline")

    Returns:
        Simulado já criado e populado, status EM_ANDAMENTO.
    """
    session = get_session()
    try:
        disciplina = session.get(Disciplina, disciplina_id)
        if not disciplina:
            raise ValueError(f"Disciplina {disciplina_id} não existe.")

        bloco_label = (
            "Conhecimentos Gerais"
            if disciplina.bloco == BlocoEdital.GERAIS
            else "Conhecimentos Específicos"
        )

        # Cria o simulado primeiro (status EM_ANDAMENTO)
        simulado = Simulado(
            usuario_id=usuario_id,
            modo=ModoSimulado.POR_DISCIPLINA,
            disciplina_id=disciplina_id,
            status=StatusSimulado.EM_ANDAMENTO,
            iniciado_em=datetime.utcnow(),
            tempo_limite_segundos=tempo_limite_segundos if com_timer else None,
            n_questoes=n_questoes,
            n_acertos=0,
        )
        session.add(simulado)
        session.flush()  # pra ter o ID

        # PASSO 1: tenta puxar do banco
        do_banco = _puxar_do_banco(session, disciplina_id, n_questoes)
        n_do_banco = len(do_banco)
        n_faltando = n_questoes - n_do_banco

        logger.info(
            "Simulado %d: %d/%d do banco, faltam %d para gerar via API",
            simulado.id, n_do_banco, n_questoes, n_faltando,
        )

        # Persiste as questões do banco (copia o conteúdo)
        ordem = 0
        for ordem, bq in enumerate(do_banco, start=1):
            session.add(Questao(
                simulado_id=simulado.id,
                sub_topico_id=bq.sub_topico_id,
                ordem=ordem,
                enunciado=bq.enunciado,
                alternativa_a=bq.alternativa_a,
                alternativa_b=bq.alternativa_b,
                alternativa_c=bq.alternativa_c,
                alternativa_d=bq.alternativa_d,
                alternativa_e=bq.alternativa_e,
                gabarito=bq.gabarito,
                justificativa=bq.justificativa,
                fonte_descricao=bq.fonte_descricao,
                fonte_url=bq.fonte_url,
                fonte_origem=bq.fonte_origem,
                alerta_revisao=bq.alerta_revisao,
            ))

        # PASSO 2: se faltam, completa via API (se permitido)
        if n_faltando > 0:
            if not permitir_api_fallback:
                raise RuntimeError(
                    f"Banco tem só {n_do_banco}/{n_questoes} questões para essa disciplina "
                    "e fallback de API está desabilitado. Adicione mais questões ao banco."
                )

            sub_topicos_para_api = _amostrar_sub_topicos(session, disciplina_id, n_faltando)
            questoes_api = _gerar_questoes_em_paralelo(
                sub_topicos=sub_topicos_para_api,
                disciplina_nome=disciplina.nome,
                bloco_label=bloco_label,
                progresso_callback=progresso_callback,
            )

            for q_data in questoes_api:
                ordem += 1
                fonte_origem = FonteOrigem.WEB if q_data.get("fonte_url") else None
                session.add(Questao(
                    simulado_id=simulado.id,
                    sub_topico_id=q_data["_sub_topico_id"],
                    ordem=ordem,
                    enunciado=q_data["enunciado"],
                    alternativa_a=q_data["alternativas"]["A"],
                    alternativa_b=q_data["alternativas"]["B"],
                    alternativa_c=q_data["alternativas"]["C"],
                    alternativa_d=q_data["alternativas"]["D"],
                    alternativa_e=q_data["alternativas"]["E"],
                    gabarito=q_data["gabarito"],
                    justificativa=q_data["justificativa"],
                    fonte_descricao=q_data.get("fonte_descricao"),
                    fonte_url=q_data.get("fonte_url"),
                    fonte_origem=fonte_origem,
                    alerta_revisao=q_data.get("alerta_revisao", False),
                ))

        # Se acabou sem nenhuma questão (banco vazio + falha geral na API), descarta
        if ordem == 0:
            session.delete(simulado)
            session.commit()
            raise RuntimeError(
                "Nenhuma questão disponível. Banco vazio para essa disciplina e "
                "geração via API falhou."
            )

        # Ajusta n_questoes ao real
        simulado.n_questoes = ordem

        session.commit()
        session.refresh(simulado)
        return simulado

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ============================================================================
# Operações durante o simulado
# ============================================================================
def simulado_em_andamento(usuario_id: int) -> Simulado | None:
    """Retorna o simulado mais recente em andamento, ou None."""
    session = get_session()
    try:
        return (
            session.query(Simulado)
            .filter_by(usuario_id=usuario_id, status=StatusSimulado.EM_ANDAMENTO)
            .order_by(Simulado.iniciado_em.desc())
            .first()
        )
    finally:
        session.close()


def get_simulado_completo(simulado_id: int) -> dict:
    """
    Carrega simulado + questões + respostas existentes para renderização.
    Retorna dict serializável (não SQLAlchemy objects, evita lazy-load issues).
    """
    session = get_session()
    try:
        simulado = session.get(Simulado, simulado_id)
        if not simulado:
            raise ValueError(f"Simulado {simulado_id} não existe.")

        questoes = (
            session.query(Questao)
            .filter_by(simulado_id=simulado_id)
            .order_by(Questao.ordem)
            .all()
        )
        respostas = (
            session.query(Resposta)
            .filter_by(simulado_id=simulado_id)
            .all()
        )
        respostas_por_questao = {r.questao_id: r for r in respostas}

        return {
            "id": simulado.id,
            "modo": simulado.modo.value,
            "disciplina_id": simulado.disciplina_id,
            "status": simulado.status.value,
            "iniciado_em": simulado.iniciado_em,
            "tempo_limite_segundos": simulado.tempo_limite_segundos,
            "n_questoes": simulado.n_questoes,
            "n_acertos": simulado.n_acertos,
            "questoes": [
                {
                    "id": q.id,
                    "ordem": q.ordem,
                    "enunciado": q.enunciado,
                    "alternativas": {
                        "A": q.alternativa_a,
                        "B": q.alternativa_b,
                        "C": q.alternativa_c,
                        "D": q.alternativa_d,
                        "E": q.alternativa_e,
                    },
                    "gabarito": q.gabarito,
                    "justificativa": q.justificativa,
                    "fonte_descricao": q.fonte_descricao,
                    "fonte_url": q.fonte_url,
                    "alerta_revisao": q.alerta_revisao,
                    "resposta": (
                        respostas_por_questao[q.id].resposta_marcada
                        if q.id in respostas_por_questao else None
                    ),
                    "marcada_revisar": (
                        respostas_por_questao[q.id].marcada_revisar
                        if q.id in respostas_por_questao else False
                    ),
                }
                for q in questoes
            ],
        }
    finally:
        session.close()


def responder_questao(
    simulado_id: int,
    questao_id: int,
    resposta_marcada: str | None,
    marcada_revisar: bool = False,
) -> None:
    """
    Autosave: UPSERT na tabela respostas.
    resposta_marcada=None significa "em branco" (apenas marcada pra revisar).
    """
    session = get_session()
    try:
        questao = session.get(Questao, questao_id)
        if not questao:
            raise ValueError(f"Questao {questao_id} não existe.")

        existing = (
            session.query(Resposta)
            .filter_by(simulado_id=simulado_id, questao_id=questao_id)
            .first()
        )

        acertou = (
            (resposta_marcada == questao.gabarito) if resposta_marcada else None
        )

        if existing:
            existing.resposta_marcada = resposta_marcada
            existing.acertou = acertou
            existing.marcada_revisar = marcada_revisar
            existing.respondida_em = datetime.utcnow() if resposta_marcada else None
        else:
            session.add(Resposta(
                simulado_id=simulado_id,
                questao_id=questao_id,
                resposta_marcada=resposta_marcada,
                acertou=acertou,
                marcada_revisar=marcada_revisar,
                respondida_em=datetime.utcnow() if resposta_marcada else None,
            ))

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def finalizar_simulado(simulado_id: int, tempo_decorrido_segundos: int) -> dict:
    """
    Marca simulado como FINALIZADO, computa acertos e retorna sumário.

    Returns:
        dict com n_acertos, total, pct_acerto, por_disciplina (dict de stats).
    """
    session = get_session()
    try:
        simulado = session.get(Simulado, simulado_id)
        if not simulado:
            raise ValueError(f"Simulado {simulado_id} não existe.")

        respostas = (
            session.query(Resposta)
            .filter_by(simulado_id=simulado_id)
            .all()
        )
        n_acertos = sum(1 for r in respostas if r.acertou)

        simulado.status = StatusSimulado.FINALIZADO
        simulado.finalizado_em = datetime.utcnow()
        simulado.tempo_decorrido_segundos = tempo_decorrido_segundos
        simulado.n_acertos = n_acertos
        session.commit()

        return {
            "simulado_id": simulado_id,
            "n_acertos": n_acertos,
            "total": simulado.n_questoes,
            "pct_acerto": (n_acertos / simulado.n_questoes * 100) if simulado.n_questoes else 0,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def descartar_simulado(simulado_id: int) -> None:
    """Marca simulado como DESCARTADO (não deleta — mantém histórico)."""
    session = get_session()
    try:
        simulado = session.get(Simulado, simulado_id)
        if not simulado:
            return
        simulado.status = StatusSimulado.DESCARTADO
        simulado.finalizado_em = datetime.utcnow()
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
