# Case Técnico Data Architect — iFood

## Objetivo

Solução de engenharia de dados para o case técnico de Data Architect do
iFood: ingestão dos dados de corridas de táxi de NY (Yellow Taxi,
Jan-Mai/2023) em um Data Lake, disponibilização para consumo via SQL, e
resposta a duas perguntas analíticas sobre os dados. O detalhamento
completo das decisões técnicas está em [`DECISOES_PROJETO.md`](DECISOES_PROJETO.md).

## Arquitetura

Modelo em camadas (medalhão simplificado), processado em **PySpark** e
persistido em **Delta Lake**, catalogado via **Unity Catalog**
(Databricks Free Edition):

- **Landing / bronze**: arquivos parquet originais, como chegaram.
- **Consumo / silver**: tabela Delta gerenciada, tipada e limpa, com um
  contrato de dados formal versionado antes da escrita (ver `contracts/`).

Data profiling e regras de qualidade de dados são etapas obrigatórias na
transição bronze → silver, e cada execução do pipeline é instrumentada
(volume, schema, lineage) — ver `DECISOES_PROJETO.md` §5-§7 para o
detalhamento dessas regras.

## Estrutura do Repositório

| Pasta/Arquivo | Propósito | Origem |
|---|---|---|
| `src/` | Código fonte do pipeline (ingestão, transformação) | Exigido pelo enunciado do case |
| `analysis/` | Scripts/notebooks com as respostas às perguntas analíticas | Exigido pelo enunciado do case |
| `contracts/` | Contratos de dados versionados das tabelas da camada de consumo | Adição do projeto — formaliza o schema/regras de qualidade da silver antes da escrita, em vez de deixá-los implícitos no código (ver Constituição, Princípio II) |
| `data/` | Landing zone local (plano B de ingestão, caso o download direto via notebook não seja viável na Free Edition); conteúdo ignorado pelo git | Adição do projeto — mitigação de risco documentada em `DECISOES_PROJETO.md` §2 |
| `specs/` | Specs versionadas do fluxo Spec-Driven Development (Spec Kit) | Adição do projeto — evidencia o processo de desenvolvimento agêntico (ver `DECISOES_PROJETO.md` §9) |
| `.specify/` | Constituição do projeto, templates e configuração do Spec Kit | Gerado pelo Spec Kit |
| `README.md` | Este arquivo | Exigido pelo enunciado do case |
| `requirements.txt` | Dependências Python fixadas para o projeto | Exigido pelo enunciado do case |

## Stack Tecnológica

- **Processamento**: PySpark (obrigatório pelo case)
- **Formato de tabela**: Delta Lake
- **Metadados/catálogo**: Unity Catalog
- **Consumo final**: SQL via Databricks SQL Warehouse
- **Plataforma**: Databricks Free Edition

Ver `requirements.txt` para as versões fixadas e `DECISOES_PROJETO.md` §2-§3
para as restrições de ambiente e justificativas.

## Como Executar

### 1. Autenticação com o Databricks

Configure o [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html)
com um perfil apontando para o workspace Free Edition:

```
databricks configure --token --profile DEFAULT
databricks current-user me --profile DEFAULT   # valida a autenticação
```

Credenciais ficam em `~/.databrickscfg` (fora do repositório, nunca
versionadas — ver `.gitignore`).

### 2. Ambiente & Landing Zone (feature 002)

Os scripts em `src/ingestion/` são escritos em formato de notebook
Databricks (`# Databricks notebook source`) e podem ser importados e
executados diretamente no workspace via CLI:

```
databricks workspace import /Workspace/Users/<seu-usuario>/ifood_case/network_check \
  --file src/ingestion/network_check.py --language PYTHON --format SOURCE --overwrite
databricks workspace import /Workspace/Users/<seu-usuario>/ifood_case/landing_zone \
  --file src/ingestion/landing_zone.py --language PYTHON --format SOURCE --overwrite
databricks workspace import /Workspace/Users/<seu-usuario>/ifood_case/land_files \
  --file src/ingestion/land_files.py --language PYTHON --format SOURCE --overwrite
```

Execute cada um como job avulso em compute serverless (`databricks jobs
submit --json '{"tasks":[{"task_key":"...", "notebook_task":{"notebook_path":"..."}}]}'`),
nesta ordem:

1. `network_check.py` — testa acesso direto à fonte NYC TLC (FR-001)
2. `landing_zone.py` — cria catalog/schema/volume da landing zone (FR-003)
3. `land_files.py` — baixa e verifica os 5 arquivos mensais (FR-004/005/006/008)

Resultado esperado, decisões tomadas e eventuais restrições encontradas
estão documentados em `DECISOES_PROJETO.md` §2. Detalhes de design em
`specs/002-ambiente-landing-zone/`.

## Perguntas Analíticas Respondidas

_Placeholder — esta seção linkará para os scripts em `analysis/` com as
respostas às duas perguntas do case (média de `total_amount` por mês, e
média de `passenger_count` por hora no mês de maio) assim que essa feature
for implementada._

## POC: Chat NL-to-SQL (Diferencial)

> ⚠️ **Isto é uma POC (prova de conceito), não um produto pronto para
> produção.** Demonstra a viabilidade de um agente conversacional
> NL-to-SQL sobre a camada silver, mas tem melhorias pendentes
> conhecidas — ver "Limitações conhecidas da POC" em
> [`specs/009-poc-app-chat/spec.md`](specs/009-poc-app-chat/spec.md).

Um [Databricks App](https://docs.databricks.com/dev-tools/databricks-apps/)
(`src/app/`) com interface de chat em português: você faz uma pergunta
em linguagem natural sobre as corridas de yellow táxi (Jan-Mai/2023), o
app gera o SQL correspondente via um modelo de linguagem
(`databricks-meta-llama-3-1-8b-instruct`), executa a consulta de
verdade na tabela `ifood_case.silver.yellow_taxi_trips` e retorna a
resposta formatada — sem que você escreva nenhum código.

- **Acesse o app**: https://poc-app-chat-3576264130915931.aws.databricksapps.com
  (requer login com uma conta do workspace Databricks)
- **Exemplos de interação já capturados**: [`src/app/examples.md`](src/app/examples.md)
- **Spec completa e limitações conhecidas**: [`specs/009-poc-app-chat/`](specs/009-poc-app-chat/)

Este app substitui o Genie Space originalmente cogitado no roadmap (ver
`DECISOES_PROJETO.md` §8 e `.specify/memory/constitution.md` v1.1.2) —
decisão tomada durante o desenvolvimento porque a configuração do Genie
é exclusiva de UI, sem caminho via CLI/API, o que quebraria o padrão
deste projeto de execução ponta a ponta automatizada.
