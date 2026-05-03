# Formato do JSON de questões

Cada questão é um objeto neste formato:

```json
{
  "disciplina": "Direito Tributário",
  "sub_topico": "Limitações constitucionais do poder de tributar",
  "enunciado": "Texto completo do enunciado, denso, estilo FCC.",
  "alternativas": {
    "A": "Texto da alternativa A...",
    "B": "Texto da alternativa B...",
    "C": "Texto da alternativa C...",
    "D": "Texto da alternativa D...",
    "E": "Texto da alternativa E..."
  },
  "gabarito": "B",
  "justificativa": "Por que B está correta e por que cada uma das demais está errada.",
  "fonte_descricao": "CF/88, art. 150, VI, 'a' e §2º",
  "fonte_url": "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm",
  "alerta_revisao": false,
  "origem": "manual"
}
```

## Regras

1. **`disciplina` e `sub_topico`** devem casar **exatamente** com a estrutura do edital (ver `db/seed_edital.py`). O script faz fallback case-insensitive, mas é melhor usar os nomes exatos.

2. **`alternativas`**: SEMPRE 5 (A-E), todas como string.

3. **`gabarito`**: uma única letra A-E.

4. **`fonte_descricao`** + **`fonte_url`**: para questões de Direito/Contabilidade Pública, sempre cite a lei/norma. URL preferencialmente `planalto.gov.br`, `cfc.org.br`, `sefaz.ce.gov.br`. Para Língua Portuguesa e Matemática pode deixar `fonte_url` em branco.

5. **`alerta_revisao`**: `true` se você tem dúvida sobre o gabarito ou sobre a fonte. O sistema vai sinalizar a questão como precisando revisão.

6. **`origem`**: sempre `"manual"` para questões geradas via Claude.ai.

## Como adicionar mais

1. Edite `questoes_iniciais.json` (ou crie um novo arquivo, ex: `questoes_lote2.json`)
2. Rode: `python -m db.seed_banco_questoes` (pega o default)
3. Ou: `python -m db.seed_banco_questoes --arquivo seed_data/questoes_lote2.json`

O script é **idempotente** — duplicatas (detectadas por matching parcial do enunciado) são ignoradas. Pode rodar quantas vezes quiser.

## Localmente vs no Streamlit Cloud

O script roda localmente (você precisa do `secrets.toml` com `DATABASE_URL` apontando pro Neon de produção). Inserir no banco local SQLite só serve pra dev — em produção é o Neon.
