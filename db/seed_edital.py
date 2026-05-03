"""
Seed do edital Sefaz CE 2026 — Área A01 (Gestão Fazendária).

Estrutura extraída do Anexo VI do edital oficial:
sface125_edital_de_abertura_final-publicar_-_docx.pdf

Para reexecutar (apaga e repopula apenas disciplinas/sub-topicos):
    python -m db.seed_edital
"""
from __future__ import annotations

from db.database import get_session, init_db
from db.models import BlocoEdital, Disciplina, SubTopico


# ----------------------------------------------------------------------------
# CONHECIMENTOS GERAIS (peso 1, 80 questões)
# ----------------------------------------------------------------------------
GERAIS = [
    {
        "nome": "Língua Portuguesa",
        "n_questoes_prova": 10,
        "sub_topicos": [
            "Redação Oficial",
            "Ortografia e acentuação",
            "Emprego do sinal indicativo de crase",
            "Compreensão e interpretação de textos de gêneros variados",
            "Relação do texto com seu contexto histórico",
            "Denotação e conotação",
            "Discurso direto, indireto e indireto livre",
            "Intertextualidade",
            "Figuras de linguagem",
            "Morfossintaxe",
            "Elementos estruturais e processos de formação de palavras",
            "Sinonímia e antonímia",
            "Pontuação",
            "Pronomes",
            "Concordância nominal e verbal",
            "Flexão nominal e verbal",
            "Vozes do verbo",
            "Correlação de tempos e modos verbais",
            "Regência nominal e verbal",
            "Coordenação e subordinação",
            "Conectivos",
            "Redação (frases corretas; equivalência e transformação de estruturas)",
        ],
    },
    {
        "nome": "Matemática Financeira/Estatística e Raciocínio Lógico",
        "n_questoes_prova": 12,
        "sub_topicos": [
            "Juros simples — montante, juros, taxa real, taxa efetiva",
            "Taxas equivalentes e capitais equivalentes (juros simples)",
            "Juros compostos — montante e juros",
            "Capitalização contínua",
            "Taxas equivalentes e capitais equivalentes (juros compostos)",
            "Descontos simples e compostos (racional e comercial)",
            "Amortizações — Sistema Francês (Price)",
            "Amortizações — Sistema de Amortização Constante (SAC)",
            "Amortizações — Sistema Misto",
            "Fluxo de caixa, valor atual e Taxa Interna de Retorno (TIR)",
            "Estatística Descritiva — gráficos, tabelas, medidas de posição e variabilidade",
            "Técnicas de contagem e Análise Combinatória",
            "Probabilidades — conceitos, espaço amostral, axiomas",
            "Distribuições discretas (Bernoulli, binomial, geométrica, Poisson)",
            "Distribuições contínuas (uniforme, normal, qui-quadrado, t de Student, F)",
            "Inferência estatística e amostragem",
            "Intervalos de confiança",
            "Testes de hipóteses para médias e proporções",
            "Correlação e regressão linear simples",
            "Raciocínio Lógico — estruturas lógicas e dedução",
            "Raciocínio verbal, matemático e sequencial",
            "Orientação espacial e temporal",
        ],
    },
    {
        "nome": "Administração e Governança Pública",
        "n_questoes_prova": 10,
        "sub_topicos": [
            "Reformas Administrativas",
            "Gestão de suprimentos e logística na administração pública",
            "Processos participativos de gestão pública (orçamento participativo, ouvidorias)",
            "Novas formas de gestão de serviços públicos e contratualização de resultados",
            "Controles interno e externo",
            "Responsabilização e Prestação de Contas",
            "Lei de Acesso à Informação (Lei 12.527/2011)",
            "Governança Pública Organizacional — conceitos, princípios, diretrizes",
            "Stakeholders da Administração Pública e teoria da agência",
            "Instâncias de Governança (estratégica, tática, operacional)",
            "Modelo de Gestão do Poder Executivo do Estado do Ceará",
            "Integridade — conceitos e Programa de Integridade do Estado do Ceará",
            "Gestão de Riscos — conceitos, modelo de três linhas",
            "Política de Gestão de Riscos do Poder Executivo do Estado do Ceará",
            "Deveres e proibições do servidor público civil do Estado do Ceará",
            "Código de Ética e Conduta da Administração Pública Estadual do Ceará",
            "Sanções éticas e disciplinares; sindicância e PAD",
            "Sistemas de correição e ética do Estado do Ceará",
            "Assédio e violência no trabalho — Convenção 190/2019 OIT",
            "Sistema de combate ao assédio moral no Poder Executivo do Estado do Ceará",
        ],
    },
    {
        "nome": "Economia",
        "n_questoes_prova": 10,
        "sub_topicos": [
            "Microeconomia — conceitos fundamentais e equilíbrio de mercado",
            "Oferta, procura e elasticidades",
            "Equilíbrio da firma e estruturas de mercado (concorrência, monopólio, oligopólio)",
            "Economia da Tributação — necessidade econômica da tributação",
            "Formas e classificação dos impostos (Ad Valorem, específicos, valor adicionado)",
            "Tributação e eficiência — eficiência de Pareto e peso morto",
            "Tributação ótima sobre mercadorias — regra de Ramsey",
            "Curva de Laffer",
            "Tributação e equidade — capacidade contributiva e benefício",
            "Incidência econômica dos tributos",
            "Tributação em concorrência perfeita e monopólio",
            "Macroeconomia — fluxo circular da renda e contabilidade nacional",
            "Agregados macroeconômicos (consumo, investimento, gastos do governo)",
            "Determinação do produto de equilíbrio — curvas IS e LM",
            "Política monetária e taxa de juros",
            "PIB real x nominal e Deflator do PIB",
            "Inflação — conceitos e formas de mensuração",
            "Contas nacionais do Brasil",
            "Balanço de Pagamentos",
            "Políticas fiscal, monetária e cambial",
            "Sistema Tributário como instrumento de distribuição de renda",
        ],
    },
    {
        "nome": "Direito Constitucional, Administrativo, Civil e Penal",
        "n_questoes_prova": 12,
        "sub_topicos": [
            # Constitucional
            "Constituição Federal de 1988 — aplicabilidade das normas constitucionais",
            "Direitos e garantias fundamentais",
            "Organização político-administrativa do Estado",
            "Administração Pública — disposições gerais e servidores",
            "Poderes Executivo, Legislativo e Judiciário",
            "Processo legislativo federal, estadual e municipal",
            "Controle de constitucionalidade",
            "Súmula vinculante e reclamação constitucional",
            "Ordem econômica e financeira",
            "Constituição do Estado do Ceará",
            # Administrativo
            "Estado, Governo e Administração Pública — conceitos",
            "Ato administrativo — requisitos, atributos, espécies, extinção",
            "Agentes públicos — provimento, vacância, direitos e deveres",
            "Poderes da Administração (hierárquico, disciplinar, regulamentar, polícia)",
            "Princípios expressos e implícitos da administração pública",
            "Responsabilidade civil do Estado",
            "Serviços Públicos — concessão, permissão, autorização",
            "Parceria Público-Privada (Leis 8.987/95 e 11.079/04)",
            "Organização Administrativa — direta e indireta",
            "Improbidade Administrativa (Lei 8.429/92)",
            "Lei Anticorrupção (Lei 12.846/13)",
            "Lei de Licitações e Contratos (Lei 14.133/21)",
            "Bens Públicos",
            "LGPD (Lei 13.709/18)",
            # Civil
            "LINDB — vigência, aplicação, conflito de leis no tempo",
            "Pessoas naturais e jurídicas — personalidade, capacidade, domicílio",
            "Bens — móveis, imóveis, públicos",
            "Negócio jurídico — disposições gerais e invalidade",
            "Prescrição e decadência",
            "Obrigações e contratos",
            "Responsabilidade civil objetiva e subjetiva",
            "Direito de exploração de propriedades (posse, usufruto, comodato)",
            "Regime de bens do casamento",
            "Sucessões — legítima, testamentária, inventário e partilha",
            # Penal
            "Princípios constitucionais e gerais do Direito Penal",
            "Aplicação da lei penal e crime",
            "Imputabilidade penal e concurso de pessoas",
            "Penas e ação penal",
            "Extinção da punibilidade",
            "Crimes contra a Fé Pública (falsidade documental)",
            "Crimes contra a Administração Pública (funcionário e particular)",
            "Crimes em licitações (Lei 14.133/21)",
            "Crimes contra a ordem tributária (Lei 8.137/90)",
            "Crime organizado (Lei 12.850/13)",
            "Lavagem de dinheiro (Lei 9.613/98)",
        ],
    },
    {
        "nome": "Direito Financeiro",
        "n_questoes_prova": 8,
        "sub_topicos": [
            "Orçamento na Constituição de 1988",
            "Plano Plurianual (PPA)",
            "Lei de Diretrizes Orçamentárias (LDO)",
            "Lei Orçamentária Anual (LOA)",
            "Princípios orçamentários",
            "Processo de aprovação da proposta orçamentária",
            "Emendas parlamentares ao Orçamento (impositivas individuais e de bancada)",
            "Créditos Adicionais",
            "LDO — objetivos, estrutura, Anexos de Metas e Riscos Fiscais",
            "Critérios para limitação de empenho",
            "LRF (LC 101/00) — Planejamento (Cap. II)",
            "LRF — Receita Pública (Cap. III)",
            "LRF — Despesa Pública (Cap. IV)",
            "LRF — Transferências Voluntárias (Cap. V)",
            "LRF — Destinação de Recursos para o Setor Privado (Cap. VI)",
            "LRF — Dívida e Endividamento (Cap. VII)",
            "LRF — Gestão Patrimonial (Cap. VIII)",
            "Lei 4.320/64 — Restos a pagar e despesas de exercícios anteriores",
            "Fundos Especiais de Despesa, Investimento e Financiamento",
            "Desvinculação de Receitas de Estados e Municípios (DREM)",
        ],
    },
    {
        "nome": "Contabilidade Geral e Pública",
        "n_questoes_prova": 10,
        "sub_topicos": [
            # Geral
            "Conceito, objetivos e usuários da informação contábil",
            "Normas Brasileiras de Contabilidade (NBC) e CPCs",
            "Itens patrimoniais — ativo, passivo, patrimônio líquido",
            "Receitas e despesas — conceitos, mensuração e contabilização",
            "Estoques — métodos de avaliação (PEPS, Média Ponderada)",
            "Tratamento contábil dos tributos em operações comerciais",
            "Ativo imobilizado — reconhecimento, mensuração, depreciação, baixa",
            "Ativo intangível — reconhecimento, mensuração, amortização, baixa",
            "Redução ao valor recuperável de ativos (impairment)",
            "Provisões, passivos contingentes e ativos contingentes",
            "Balanço patrimonial — estrutura e classificação",
            "Demonstração do resultado e resultado abrangente",
            "Demonstração das mutações do patrimônio líquido",
            # Pública
            "Lei 4.320/64 e suas alterações",
            "MCASP (11ª edição) — Procedimentos Contábeis Orçamentários",
            "MCASP — Procedimentos Contábeis Patrimoniais",
            "MCASP — Procedimentos Contábeis Específicos",
            "MCASP — Demonstrações Contábeis Aplicadas ao Setor Público",
            "Plano de Contas Aplicado ao Setor Público (PCASP)",
            "NBC TSP — Estrutura Conceitual",
            "NBC TSP 01 a 11 (provisões, ativos, intangíveis, imobilizado)",
            "NBC TSP 12 a 22 (receitas, custos, demonstrações)",
            "NBC TSP 23 a 34 (consolidação, partes relacionadas, participações)",
            "Decreto 10.540/2020 (SIAFIC)",
        ],
    },
    {
        "nome": "Auditoria",
        "n_questoes_prova": 8,
        "sub_topicos": [
            "Distinção entre auditoria interna, independente e perícia contábil",
            "Planejamento da auditoria",
            "Fraude e erro",
            "Relevância (materialidade) na auditoria",
            "Riscos da auditoria",
            "Amostragem — tamanho, tipos e avaliação dos resultados",
            "Procedimentos de auditoria",
            "Confirmações externas",
            "Testes de observância (controles)",
            "Estudo e avaliação do sistema contábil e de controles internos",
            "Testes substantivos",
            "Estimativas contábeis",
            "Auditoria de estoque (interna, externa, sistemas, fluxo)",
            "Papéis de trabalho e documentação de auditoria",
            "Evidência em auditoria",
            "Pareceres de auditoria",
            "NBC TA 230, 240, 265, 300, 315, 320 (planejamento e riscos)",
            "NBC TA 500, 501, 505, 530, 540 (evidência, amostragem, estimativas)",
            "NBC TA 610, 620, 700 (uso de outros auditores e parecer)",
        ],
    },
]

# ----------------------------------------------------------------------------
# CONHECIMENTOS ESPECÍFICOS — Área A01 Gestão Fazendária (peso 2, 80 questões)
# ----------------------------------------------------------------------------
ESPECIFICOS = [
    {
        "nome": "Direito Tributário",
        "n_questoes_prova": 20,
        "sub_topicos": [
            "Sistema Tributário Nacional na CF/88 — princípios gerais",
            "Limitações constitucionais do poder de tributar",
            "Impostos da União, Estados, DF e Municípios",
            "Imposto de competência compartilhada (IBS)",
            "Repartição das receitas tributárias",
            "CTN — Sistema Tributário Nacional (disposições gerais)",
            "Competência tributária — disposições gerais e especiais",
            "Impostos sobre patrimônio, renda e transmissão",
            "Taxas e Contribuição de Melhoria",
            "Legislação Tributária — leis, tratados, decretos, normas complementares",
            "Vigência da legislação tributária",
            "Aplicação da legislação tributária",
            "Interpretação e integração da legislação tributária",
            "Obrigação tributária — fato gerador, sujeito ativo e passivo",
            "Solidariedade, capacidade tributária, domicílio tributário",
            "Responsabilidade tributária — sucessores, terceiros, infrações",
            "Crédito tributário — constituição e lançamento",
            "Modalidades de lançamento (ofício, declaração, homologação)",
            "Suspensão da exigibilidade do crédito tributário",
            "Moratória",
            "Extinção do crédito tributário — pagamento, compensação, prescrição",
            "Pagamento indevido e repetição",
            "Exclusão do crédito — isenção e anistia",
            "Garantias e privilégios do crédito tributário",
            "Administração tributária — fiscalização e dívida ativa",
            "Certidões negativas",
        ],
    },
    {
        "nome": "Legislação Tributária",
        "n_questoes_prova": 20,
        "sub_topicos": [
            "LC 24/1975 — convênios para isenções de ICMS",
            "LC 87/1996 (Lei Kandir) — ICMS",
            "LC 105/2001 — sigilo bancário",
            "LC 116/2003 — ISSQN e conflito de competência com ICMS",
            "LC 123/2006 — Estatuto da Microempresa e Simples Nacional",
            "Resolução CGSN 140/2018 — Simples Nacional",
            "LC 160/2017 — convênio sobre remissão e benefícios fiscais",
            "LC 192/2022 — combustíveis (ICMS monofásico)",
            "EC 132/2023 — Reforma Tributária",
            "LC 214/2025 — IBS e CBS",
            "Comitê Gestor do IBS",
            "Contribuição sobre Bens e Serviços (CBS)",
            "LC 227/2026 — administração e gestão do IBS",
            "Lei CE 18.665/2023 — ICMS Ceará",
            "Decreto CE 33.327/2019 — RICMS",
            "Lei CE 15.812/2015 — ITCD Ceará",
            "Lei CE 12.023/1992 — IPVA Ceará",
            "LC CE 37/2003 — FECOP",
            "ICMS-CE — fato gerador, base de cálculo, alíquotas",
            "ICMS-CE — substituição tributária",
            "ICMS-CE — diferencial de alíquota (DIFAL)",
            "ICMS-CE — não cumulatividade e crédito",
            "ICMS-CE — obrigações acessórias e documentos fiscais",
            "ITCD-CE — fato gerador e cálculo",
            "IPVA-CE — fato gerador e cálculo",
        ],
    },
    {
        "nome": "Contabilidade Avançada e de Custos",
        "n_questoes_prova": 20,
        "sub_topicos": [
            # Avançada
            "Políticas contábeis, mudança de estimativa e retificação de erro",
            "Mensuração a Valor Justo — conceitos e tratamento",
            "Ajuste a valor presente",
            "Instrumentos financeiros — conceito e tratamento contábil",
            "Valores a receber, aplicações financeiras",
            "Empréstimos e debêntures",
            "Propriedade para investimento",
            "Operações de arrendamento (leasing)",
            "Participações societárias — coligadas e controladas",
            "Influência significativa e controle",
            "Métodos de avaliação (custo, equivalência patrimonial)",
            "Mais valia, goodwill e compra com deságio",
            "Subvenção e assistência governamentais",
            "Conversão de demonstrações contábeis (taxas de câmbio)",
            "Demonstração dos Fluxos de Caixa",
            "Demonstração do Valor Adicionado",
            # Custos
            "Conceitos e terminologia da contabilidade de custos",
            "Custos diretos e indiretos",
            "Custos fixos e variáveis",
            "Custeio por absorção",
            "Custeio variável (direto)",
            "Custeio Baseado em Atividades (ABC)",
            "Departamentalização — conceitos e tratamento",
            "Produção por ordem, contínua e conjunta",
            "Apuração do custo da produção acabada e produtos vendidos",
            "Custo padrão — conceito e tratamento",
            "Margem de contribuição",
            "Relação custo-volume-lucro",
            "Ponto de equilíbrio (contábil, econômico, financeiro)",
            "Margem de segurança",
        ],
    },
    {
        "nome": "Fluência de Dados",
        "n_questoes_prova": 10,
        "sub_topicos": [
            "Conceitos fundamentais de Ciência de Dados",
            "Tipos de dados — estruturados, não estruturados, semiestruturados",
            "Ciclo de vida da informação e Metodologia CRISP-DM",
            "Big Data — Data Warehouse, Data Mart, Data Lake, Data Lakehouse",
            "Engenharia de Dados",
            "Pré-processamento — preparação, limpeza, transformação",
            "Bancos de dados relacionais e NoSQL",
            "SQL — DQL, agregação, agrupamento, junção, ordenação",
            "Análise de dados — agrupamentos, tendências, projeções",
            "Data Mining",
            "Aprendizado de Máquina (Machine Learning) — noções",
            "Aprendizado Profundo (Deep Learning) — noções",
            "Inteligência Artificial e Processamento de Linguagem Natural",
            "Governança de Dados — conceito, tipos, papéis",
            "Governança e Ética em IA — transparência, responsabilidade, viés",
            "Segurança da Informação — confidencialidade, integridade, disponibilidade",
            "Classificação e controle de acesso a dados",
            "Anonimização, mascaramento, retenção de dados",
            "LGPD (Lei 13.709/2018) — conformidade",
            "Marco Civil da Internet",
            "Sigilo Fiscal e funcional (CTN art. 198-199)",
        ],
    },
    {
        "nome": "Finanças Públicas",
        "n_questoes_prova": 10,
        "sub_topicos": [
            "Objetivos, metas e definição de Finanças Públicas",
            "Visão clássica das funções do Estado",
            "Evolução das funções do Governo",
            "Falhas de mercado, bens públicos e externalidades",
            "Papel do Governo na economia",
            "Objetivos da política fiscal",
            "Funções alocativa, distributiva e estabilizadora",
            "Financiamento dos gastos públicos — tributação e equidade",
            "Tipos de tributos",
            "Conceito de déficit público e formas de financiamento",
            "Resultado Fiscal — Necessidade de Financiamento do Setor Público (NFSP)",
            "Resultado Primário",
            "Resultado Nominal",
        ],
    },
]


# ----------------------------------------------------------------------------
# Execução
# ----------------------------------------------------------------------------
def seed():
    init_db()
    session = get_session()

    # Limpa apenas estrutura do edital (preserva simulados, respostas, etc.)
    session.query(SubTopico).delete()
    session.query(Disciplina).delete()
    session.commit()

    ordem_disc = 0

    for dados in GERAIS:
        ordem_disc += 1
        disc = Disciplina(
            nome=dados["nome"],
            bloco=BlocoEdital.GERAIS,
            peso=1,
            n_questoes_prova=dados["n_questoes_prova"],
            ordem=ordem_disc,
        )
        session.add(disc)
        session.flush()
        for i, st in enumerate(dados["sub_topicos"], start=1):
            session.add(SubTopico(disciplina_id=disc.id, nome=st, ordem=i))

    for dados in ESPECIFICOS:
        ordem_disc += 1
        disc = Disciplina(
            nome=dados["nome"],
            bloco=BlocoEdital.ESPECIFICOS,
            peso=2,
            n_questoes_prova=dados["n_questoes_prova"],
            ordem=ordem_disc,
        )
        session.add(disc)
        session.flush()
        for i, st in enumerate(dados["sub_topicos"], start=1):
            session.add(SubTopico(disciplina_id=disc.id, nome=st, ordem=i))

    session.commit()

    n_disc = session.query(Disciplina).count()
    n_sub = session.query(SubTopico).count()
    print(f"Seed concluído: {n_disc} disciplinas, {n_sub} sub-tópicos.")


if __name__ == "__main__":
    seed()
