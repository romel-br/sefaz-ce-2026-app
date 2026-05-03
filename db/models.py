"""
Modelo de dados (SQLAlchemy) para o app Sefaz CE 2026.

Estrutura geral:
- Usuario: Ariane (estudante) e Romel (admin)
- Disciplina e SubTopico: estrutura do edital, populada via seed
- Simulado: cada execução de prova (modo, status, tempo)
- Questao: questão gerada para um simulado, com fonte
- Resposta: resposta da Ariane a uma questão dentro de um simulado
- MaterialEstudo: material gerado pós-simulado para áreas fracas
- ComentarioMaterial: anotações livres da Ariane sobre cada material
- HistoricoNP: snapshot do score após cada simulado, para evolução temporal
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum as PyEnum


def _utcnow() -> datetime:
    """Wrapper para `datetime.now(timezone.utc)` — substitui `datetime.utcnow()` deprecated em 3.12+."""
    return datetime.now(timezone.utc)

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --------------------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------------------
class PerfilUsuario(str, PyEnum):
    ESTUDANTE = "estudante"
    ADMIN = "admin"


class BlocoEdital(str, PyEnum):
    GERAIS = "gerais"
    ESPECIFICOS = "especificos"


class ModoSimulado(str, PyEnum):
    DIAGNOSTICO = "diagnostico"        # 160q, 5h — primeiro simulado obrigatório
    POR_DISCIPLINA = "por_disciplina"  # uma disciplina específica
    AREAS_FRACAS = "areas_fracas"      # foco nos sub-tópicos com proficiência <70%
    COMPLETO = "completo"              # 160q, 5h — não é o primeiro


class StatusSimulado(str, PyEnum):
    EM_ANDAMENTO = "em_andamento"
    FINALIZADO = "finalizado"
    DESCARTADO = "descartado"


class FonteOrigem(str, PyEnum):
    LOCAL = "local"      # da pasta /fontes_oficiais
    WEB = "web"          # busca em domínio whitelist
    DOUTRINA = "doutrina"  # interpretação doutrinária


# --------------------------------------------------------------------------------------
# Modelos
# --------------------------------------------------------------------------------------
class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    perfil: Mapped[PerfilUsuario] = mapped_column(Enum(PerfilUsuario), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    simulados: Mapped[list["Simulado"]] = relationship(back_populates="usuario")


class Disciplina(Base):
    __tablename__ = "disciplinas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    bloco: Mapped[BlocoEdital] = mapped_column(Enum(BlocoEdital), nullable=False)
    peso: Mapped[int] = mapped_column(Integer, nullable=False)              # 1 ou 2
    n_questoes_prova: Mapped[int] = mapped_column(Integer, nullable=False)  # quantas na prova real
    ordem: Mapped[int] = mapped_column(Integer, default=0)                  # exibição no UI

    sub_topicos: Mapped[list["SubTopico"]] = relationship(back_populates="disciplina", cascade="all, delete-orphan")


class SubTopico(Base):
    __tablename__ = "sub_topicos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    disciplina_id: Mapped[int] = mapped_column(ForeignKey("disciplinas.id"), nullable=False)
    nome: Mapped[str] = mapped_column(String(300), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, default=0)

    disciplina: Mapped[Disciplina] = relationship(back_populates="sub_topicos")
    questoes: Mapped[list["Questao"]] = relationship(back_populates="sub_topico")


class Simulado(Base):
    __tablename__ = "simulados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    modo: Mapped[ModoSimulado] = mapped_column(Enum(ModoSimulado), nullable=False)
    disciplina_id: Mapped[int | None] = mapped_column(ForeignKey("disciplinas.id"), nullable=True)
    status: Mapped[StatusSimulado] = mapped_column(Enum(StatusSimulado), default=StatusSimulado.EM_ANDAMENTO)

    iniciado_em: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    finalizado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tempo_decorrido_segundos: Mapped[int] = mapped_column(Integer, default=0)
    tempo_limite_segundos: Mapped[int | None] = mapped_column(Integer, nullable=True)

    n_questoes: Mapped[int] = mapped_column(Integer, nullable=False)
    n_acertos: Mapped[int] = mapped_column(Integer, default=0)

    usuario: Mapped[Usuario] = relationship(back_populates="simulados")
    disciplina: Mapped[Disciplina | None] = relationship()
    questoes: Mapped[list["Questao"]] = relationship(back_populates="simulado", cascade="all, delete-orphan")
    respostas: Mapped[list["Resposta"]] = relationship(back_populates="simulado", cascade="all, delete-orphan")
    historico_np: Mapped["HistoricoNP | None"] = relationship(back_populates="simulado", uselist=False)
    materiais: Mapped[list["MaterialEstudo"]] = relationship(back_populates="simulado_origem")


class Questao(Base):
    __tablename__ = "questoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulado_id: Mapped[int] = mapped_column(ForeignKey("simulados.id"), nullable=False)
    sub_topico_id: Mapped[int] = mapped_column(ForeignKey("sub_topicos.id"), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)

    enunciado: Mapped[str] = mapped_column(Text, nullable=False)
    alternativa_a: Mapped[str] = mapped_column(Text, nullable=False)
    alternativa_b: Mapped[str] = mapped_column(Text, nullable=False)
    alternativa_c: Mapped[str] = mapped_column(Text, nullable=False)
    alternativa_d: Mapped[str] = mapped_column(Text, nullable=False)
    alternativa_e: Mapped[str] = mapped_column(Text, nullable=False)
    gabarito: Mapped[str] = mapped_column(String(1), nullable=False)  # A, B, C, D ou E
    justificativa: Mapped[str] = mapped_column(Text, nullable=False)

    fonte_descricao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fonte_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fonte_origem: Mapped[FonteOrigem | None] = mapped_column(Enum(FonteOrigem), nullable=True)
    alerta_revisao: Mapped[bool] = mapped_column(Boolean, default=False)

    simulado: Mapped[Simulado] = relationship(back_populates="questoes")
    sub_topico: Mapped[SubTopico] = relationship(back_populates="questoes")
    resposta: Mapped["Resposta | None"] = relationship(back_populates="questao", uselist=False)


class Resposta(Base):
    __tablename__ = "respostas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulado_id: Mapped[int] = mapped_column(ForeignKey("simulados.id"), nullable=False)
    questao_id: Mapped[int] = mapped_column(ForeignKey("questoes.id"), nullable=False, unique=True)

    resposta_marcada: Mapped[str | None] = mapped_column(String(1), nullable=True)  # A-E ou null se em branco
    acertou: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    tempo_gasto_segundos: Mapped[int] = mapped_column(Integer, default=0)
    marcada_revisar: Mapped[bool] = mapped_column(Boolean, default=False)

    respondida_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    simulado: Mapped[Simulado] = relationship(back_populates="respostas")
    questao: Mapped[Questao] = relationship(back_populates="resposta")


class MaterialEstudo(Base):
    __tablename__ = "materiais_estudo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulado_origem_id: Mapped[int] = mapped_column(ForeignKey("simulados.id"), nullable=False)
    disciplina_id: Mapped[int] = mapped_column(ForeignKey("disciplinas.id"), nullable=False)

    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    conteudo_md: Mapped[str] = mapped_column(Text, nullable=False)
    fontes_citadas: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON com lista de URLs

    gerado_em: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    simulado_origem: Mapped[Simulado] = relationship(back_populates="materiais")
    disciplina: Mapped[Disciplina] = relationship()
    comentarios: Mapped[list["ComentarioMaterial"]] = relationship(back_populates="material", cascade="all, delete-orphan")


class ComentarioMaterial(Base):
    __tablename__ = "comentarios_material"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materiais_estudo.id"), nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    material: Mapped[MaterialEstudo] = relationship(back_populates="comentarios")


class BancoQuestao(Base):
    """
    Pool de questões pré-geradas, NÃO vinculadas a um simulado específico.

    Origem possível:
    - "manual": gerada via Claude.ai (conversa do Romel) e seedada via JSON
    - "api": gerada via API (legacy, caso queira popular o banco com a API)

    Quando um simulado é criado, sorteia daqui primeiro. Se não houver questões
    suficientes para a disciplina, completa via API generation.
    """
    __tablename__ = "banco_questoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sub_topico_id: Mapped[int] = mapped_column(ForeignKey("sub_topicos.id"), nullable=False)

    enunciado: Mapped[str] = mapped_column(Text, nullable=False)
    alternativa_a: Mapped[str] = mapped_column(Text, nullable=False)
    alternativa_b: Mapped[str] = mapped_column(Text, nullable=False)
    alternativa_c: Mapped[str] = mapped_column(Text, nullable=False)
    alternativa_d: Mapped[str] = mapped_column(Text, nullable=False)
    alternativa_e: Mapped[str] = mapped_column(Text, nullable=False)
    gabarito: Mapped[str] = mapped_column(String(1), nullable=False)
    justificativa: Mapped[str] = mapped_column(Text, nullable=False)

    fonte_descricao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fonte_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fonte_origem: Mapped[FonteOrigem | None] = mapped_column(Enum(FonteOrigem), nullable=True)
    alerta_revisao: Mapped[bool] = mapped_column(Boolean, default=False)

    origem: Mapped[str] = mapped_column(String(20), default="manual")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    sub_topico: Mapped[SubTopico] = relationship()


class HistoricoNP(Base):
    __tablename__ = "historico_np"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulado_id: Mapped[int] = mapped_column(ForeignKey("simulados.id"), nullable=False, unique=True)

    np_gerais: Mapped[float] = mapped_column(Float, nullable=False)
    np_especificos: Mapped[float] = mapped_column(Float, nullable=False)
    score_final: Mapped[float] = mapped_column(Float, nullable=False)
    faixa_chance: Mapped[str] = mapped_column(String(50), nullable=False)

    acertos_gerais: Mapped[int] = mapped_column(Integer, default=0)
    acertos_especificos: Mapped[int] = mapped_column(Integer, default=0)

    calculado_em: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    simulado: Mapped[Simulado] = relationship(back_populates="historico_np")
