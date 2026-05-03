# App de Preparação Sefaz CE 2026 — Ariane

Aplicação Streamlit + Python para apoiar a preparação da Ariane para o concurso **Sefaz CE 2026** (Auditor-Fiscal da Fazenda Estadual, Área A01 — Gestão Fazendária).

Plano técnico completo: [`../PLANO_APP_SEFAZ_CE_2026.md`](../PLANO_APP_SEFAZ_CE_2026.md)

---

## Estrutura do projeto

```
app/
├── app.py                          # Ponto de entrada Streamlit
├── requirements.txt                # Dependências Python
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example        # Template — copiar para secrets.toml
├── config/
│   ├── fontes_confiaveis.yml       # Whitelist de domínios para RAG
│   ├── parametros_np.yml           # Médias, DP, faixas de chance
│   └── prompts.yml                 # Prompts versionados da Claude API
├── db/
│   ├── models.py                   # Schema SQLAlchemy
│   ├── database.py                 # Conexão (SQLite local ou Turso)
│   └── seed_edital.py              # Popula 13 disciplinas + sub-tópicos
├── modules/
│   ├── auth.py                     # Login com bcrypt + secrets
│   └── config_loader.py            # Carrega YAMLs com cache
├── pages/                          # (vazio — páginas Streamlit serão adicionadas)
└── fontes_oficiais/                # (vazio — PDFs oficiais serão adicionados)
```

---

## Setup — passo a passo

### 1. Pré-requisitos

- Conta GitHub (gratuita)
- Conta Anthropic com API key e crédito mínimo
- Conta Streamlit Cloud (gratuita)
- Conta Turso (gratuita) — banco de dados na nuvem

### 2. Configurar `secrets.toml`

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edite `.streamlit/secrets.toml`:
- `ANTHROPIC_API_KEY`: sua API key da Anthropic
- `DATABASE_URL`: deixar `sqlite:///db/local.db` para dev; Turso em produção
- `[users.ariane]` e `[users.romel]`: usuário, nome, hash bcrypt da senha, perfil

### 3. Gerar hash de senha

```bash
python -c "import bcrypt; print(bcrypt.hashpw(b'sua_senha_aqui', bcrypt.gensalt()).decode())"
```

Cole o resultado no campo `senha_hash` do respectivo usuário.

### 4. Rodar localmente (opcional)

```bash
pip install -r requirements.txt
streamlit run app.py
```

O app abrirá em http://localhost:8501.

### 5. Deploy no Streamlit Cloud

1. Subir o projeto para um repositório GitHub
2. Em https://share.streamlit.io → New app → escolher repo, branch e `app.py`
3. Em **Advanced settings → Secrets**, colar o conteúdo do seu `secrets.toml` local
4. Deploy. URL pública gerada automaticamente

---

## Banco de dados

**Dev:** SQLite em `db/local.db` (criado automaticamente, não vai para o Git).

**Produção (Streamlit Cloud + Turso):**
1. Criar banco em https://turso.tech (CLI ou dashboard)
2. Gerar token de acesso
3. Em `secrets.toml` (ou no Streamlit Cloud Secrets):
   ```
   DATABASE_URL = "sqlite+libsql://NOME-do-banco-USUARIO.turso.io?authToken=TOKEN"
   ```

O schema é criado automaticamente no primeiro acesso. O seed do edital roda só se a tabela `disciplinas` estiver vazia.

---

## Próximas etapas (ver plano técnico)

1. Motor de geração de questões estilo FCC (Claude API + RAG)
2. Motor de cálculo da Nota Padronizada (NP)
3. Telas de simulado (3 modos)
4. Tela de resultado pós-simulado
5. Motor de geração de material de estudo
6. Dashboard gerencial
7. Aba de feedbacks consolidados (admin)

---

## Stack

- **Python 3.11+** | **Streamlit 1.40+**
- **SQLAlchemy 2.0** + **SQLite** (dev) / **libSQL/Turso** (prod)
- **Claude API** (Anthropic) — geração de questões e material
- **Plotly** — gráficos do dashboard
- **bcrypt** — hash de senhas
