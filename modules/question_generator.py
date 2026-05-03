"""
Motor de geração de questões estilo FCC.

Usa Claude API (claude-opus-4-7) com:
- Adaptive thinking + effort=high
- Web search restrito à whitelist de domínios oficiais
- Prompt cache na system prompt (reaproveitamento entre chamadas)
- Output estruturado via JSON schema

Fluxo:
1. Carrega prompts versionados de config/prompts.yml
2. Carrega whitelist de domínios de config/fontes_confiaveis.yml
3. Chama Claude com web_search habilitado e restrito
4. Parseia o JSON da resposta final
5. Retorna lista de questões + metadados (usage, fontes consultadas)

Uso:
    from modules.question_generator import gerar_questoes
    result = gerar_questoes(
        disciplina="Direito Tributário",
        sub_topico="Limitações constitucionais do poder de tributar",
        bloco="Conhecimentos Específicos",
        quantidade=2,
    )
    print(result["questoes"])
"""
from __future__ import annotations

import json
import logging
from typing import Any

from modules.claude_client import get_client
from modules.config_loader import fontes_confiaveis, prompts

logger = logging.getLogger(__name__)

MODEL = "claude-opus-4-7"
MAX_TOKENS = 16000  # Folga generosa para thinking + ferramentas + output


def _allowed_domains() -> list[str]:
    """Combina domínios oficiais + doutrina da whitelist."""
    fontes = fontes_confiaveis()
    return fontes["dominios_oficiais"] + fontes["dominios_doutrina"]


def _json_schema_questoes() -> dict[str, Any]:
    """Schema rígido para o output. additionalProperties=false em todos os níveis (requisito de structured outputs)."""
    return {
        "type": "object",
        "properties": {
            "questoes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "enunciado": {"type": "string"},
                        "alternativas": {
                            "type": "object",
                            "properties": {
                                "A": {"type": "string"},
                                "B": {"type": "string"},
                                "C": {"type": "string"},
                                "D": {"type": "string"},
                                "E": {"type": "string"},
                            },
                            "required": ["A", "B", "C", "D", "E"],
                            "additionalProperties": False,
                        },
                        "gabarito": {"type": "string", "enum": ["A", "B", "C", "D", "E"]},
                        "justificativa": {"type": "string"},
                        "fonte_descricao": {"type": "string"},
                        "fonte_url": {"type": "string"},  # vazio se não houver URL
                        "alerta_revisao": {"type": "boolean"},
                    },
                    "required": [
                        "enunciado",
                        "alternativas",
                        "gabarito",
                        "justificativa",
                        "fonte_descricao",
                        "fonte_url",
                        "alerta_revisao",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["questoes"],
        "additionalProperties": False,
    }


def gerar_questoes(
    disciplina: str,
    sub_topico: str,
    bloco: str,
    quantidade: int = 1,
    nivel: str = "medio",
) -> dict[str, Any]:
    """
    Gera N questões estilo FCC para um sub-tópico.

    Args:
        disciplina: Nome da disciplina (ex: "Direito Tributário")
        sub_topico: Sub-tópico específico (ex: "Limitações constitucionais...")
        bloco: "Conhecimentos Gerais" ou "Conhecimentos Específicos"
        quantidade: Quantas questões gerar (1-5 recomendado por chamada)
        nivel: "facil" | "medio" | "dificil"

    Returns:
        dict com:
        - questoes: list de dicts no schema (enunciado, alternativas, gabarito, ...)
        - usage: dict com tokens consumidos (input, output, cache_read, cache_creation)
        - stop_reason: razão final da parada
    """
    client = get_client()
    cfg = prompts()

    system_prompt = cfg["geracao_questoes"]["system"]
    user_prompt = cfg["geracao_questoes"]["user_template"].format(
        disciplina=disciplina,
        sub_topico=sub_topico,
        bloco=bloco,
        quantidade=quantidade,
        nivel=nivel,
    )

    # Web search restrito à whitelist
    web_search_tool = {
        "type": "web_search_20260209",
        "name": "web_search",
        "allowed_domains": _allowed_domains(),
        "max_uses": 5,  # bound de buscas por requisição (cost guard)
    }

    logger.info(
        "Gerando %d questões: disciplina=%s, sub_topico=%s",
        quantidade, disciplina, sub_topico,
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        # System prompt cacheado: economiza ~70% em batches
        cache_control={"type": "ephemeral"},
        system=[
            {
                "type": "text",
                "text": system_prompt,
            }
        ],
        thinking={"type": "adaptive"},
        output_config={
            "effort": "high",  # Mínimo recomendado para tarefas intelligence-sensitive em 4.7
            "format": {
                "type": "json_schema",
                "schema": _json_schema_questoes(),
            },
        },
        tools=[web_search_tool],
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Trata pause_turn (web_search server-side hit iteration limit) — re-envia para continuar
    while response.stop_reason == "pause_turn":
        logger.info("pause_turn recebido, re-enviando para continuar agentic loop")
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            cache_control={"type": "ephemeral"},
            system=[{"type": "text", "text": system_prompt}],
            thinking={"type": "adaptive"},
            output_config={
                "effort": "high",
                "format": {"type": "json_schema", "schema": _json_schema_questoes()},
            },
            tools=[web_search_tool],
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": response.content},
            ],
        )

    # Extrai o text block final (que estará no formato JSON garantido pelo schema)
    text_blocks = [b for b in response.content if b.type == "text"]
    if not text_blocks:
        raise RuntimeError(
            f"Resposta sem text block. stop_reason={response.stop_reason}, "
            f"content_types={[b.type for b in response.content]}"
        )

    json_text = text_blocks[-1].text  # Último text é a resposta estruturada
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error("Falha parseando JSON: %s\n--- raw ---\n%s", e, json_text[:500])
        raise

    return {
        "questoes": parsed["questoes"],
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cache_creation_input_tokens": getattr(
                response.usage, "cache_creation_input_tokens", 0
            ),
            "cache_read_input_tokens": getattr(
                response.usage, "cache_read_input_tokens", 0
            ),
        },
        "stop_reason": response.stop_reason,
        "model": response.model,
    }
