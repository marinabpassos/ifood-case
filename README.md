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

**Padrão comum aos passos 2-4, 6 e 8 abaixo**: cada `databricks jobs
submit` retorna um `run_id`; para ver o resultado (JSON com métricas,
contagens etc.), rode `databricks jobs get-run-output <run-id> --profile
DEFAULT` depois que o job terminar (`databricks jobs get-run <run-id>
--profile DEFAULT` para acompanhar o status).

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

### 3. Data Profiling (feature 003)

EDA sobre a landing zone, antes de qualquer transformação:

```
databricks workspace import /Workspace/Users/<seu-usuario>/ifood_case/schema_check \
  --file src/profiling/schema_check.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"schema_check","notebook_task":{"notebook_path":"/Workspace/Users/<seu-usuario>/ifood_case/schema_check"}}]}'

databricks workspace import /Workspace/Users/<seu-usuario>/ifood_case/profile_bronze \
  --file src/profiling/profile_bronze.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"profile_bronze","notebook_task":{"notebook_path":"/Workspace/Users/<seu-usuario>/ifood_case/profile_bronze"}}]}'
```

Resultado documentado em `specs/003-data-profiling/findings.md`. Passo a
passo completo em `specs/003-data-profiling/quickstart.md`.

### 4. Camada Bronze (feature 004)

Move a landing zone para seu próprio schema e ingere na tabela Delta
bronze (1:1 com a fonte, sem regra de negócio):

```
databricks workspace import /Workspace/Users/<seu-usuario>/ifood_case/rename_landing_schema \
  --file src/bronze/rename_landing_schema.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"rename_landing_schema","notebook_task":{"notebook_path":"/Workspace/Users/<seu-usuario>/ifood_case/rename_landing_schema"}}]}'

databricks workspace import /Workspace/Users/<seu-usuario>/ifood_case/ingest_bronze \
  --file src/bronze/ingest_bronze.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"ingest_bronze","notebook_task":{"notebook_path":"/Workspace/Users/<seu-usuario>/ifood_case/ingest_bronze"}}]}'
```

Resultado documentado em `specs/004-bronze-layer/ingestion-log.md`.
Passo a passo completo em `specs/004-bronze-layer/quickstart.md`.

### 5. Contrato de Dados da Silver (feature 005)

Roda 100% local, sem acessar o Databricks:

```
pip install -r requirements.txt
python src/contracts/validate_silver_contract.py
```

Contrato versionado em [`contracts/nyc_taxi_silver.yaml`](contracts/nyc_taxi_silver.yaml)
(schema, grão, regras de qualidade e política de versionamento).

### 6. Data Quality & Camada Silver (feature 006)

Aplica as regras de qualidade do contrato sobre a bronze e escreve a
tabela Delta silver tipada e limpa:

```
databricks workspace import /Workspace/Users/<seu-usuario>/ifood_case/build_silver \
  --file src/silver/build_silver.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"build_silver","notebook_task":{"notebook_path":"/Workspace/Users/<seu-usuario>/ifood_case/build_silver"}}]}'
```

Resultado documentado em `specs/006-silver-data-quality/dq-run-log.md`.
Passo a passo completo em `specs/006-silver-data-quality/quickstart.md`.

### 7. Observability da Pipeline (feature 007)

Reexecute bronze e silver (passos 4 e 6 acima, scripts já instrumentados)
e consulte o log de execuções:

```sql
SELECT pipeline_stage, executed_at, status, rows_read, rows_written,
       schema_check_status, duration_seconds, metrics, alerts
FROM ifood_case.silver._pipeline_run_log
ORDER BY executed_at;
```

Lineage nativo (landing → bronze → silver) via Catalog Explorer ou
`system.access.table_lineage`. Detalhes em
`specs/007-pipeline-observability/quickstart.md`.

### 8. Perguntas Analíticas (feature 008)

As duas queries obrigatórias rodam direto, sem notebook:

```
databricks experimental aitools tools query "$(cat analysis/avg_total_amount_by_month.sql)" --profile DEFAULT
databricks experimental aitools tools query "$(cat analysis/avg_passenger_count_by_hour_may.sql)" --profile DEFAULT
```

Opcionalmente, o notebook `analysis/analise.py` regera os gráficos (e o
bônus de sazonalidade):

```
databricks workspace import /Workspace/Users/<seu-usuario>/ifood_case/analise \
  --file analysis/analise.py --language PYTHON --format SOURCE --overwrite
databricks jobs submit --json '{"tasks":[{"task_key":"analise","notebook_task":{"notebook_path":"/Workspace/Users/<seu-usuario>/ifood_case/analise"}}]}'
```

Resultado completo em [`analysis/answers.md`](analysis/answers.md). Passo
a passo completo em `specs/008-analytical-questions/quickstart.md`.

## Perguntas Analíticas Respondidas

Calculadas diretamente sobre `ifood_case.silver.yellow_taxi_trips`
(features 004-006), sem filtragem ou limpeza adicional — a tabela já
está pronta para análise. Detalhes completos (tabelas mês a mês/hora a
hora, gráficos) em [`analysis/answers.md`](analysis/answers.md).

1. **Média de `total_amount` por mês** — sobe de ~$27.46 em janeiro para
   ~$29.45 em maio, com uma pequena queda em fevereiro. Query:
   [`analysis/avg_total_amount_by_month.sql`](analysis/avg_total_amount_by_month.sql).
2. **Média de `passenger_count` por hora do dia, em maio** — varia pouco
   ao longo do dia (entre 1.26 e 1.46), mais baixa no início da manhã
   (hora 6) e mais alta de madrugada (hora 2). Query:
   [`analysis/avg_passenger_count_by_hour_may.sql`](analysis/avg_passenger_count_by_hour_may.sql).

Ambas as queries são standalone, rodáveis por qualquer pessoa com acesso
ao SQL Warehouse — sem depender de notebook. Um notebook Databricks
completo (`analysis/analise.py`) gera os gráficos das duas respostas
acima e, como diferencial, uma decomposição de tendência/sazonalidade
semanal do volume diário de corridas (Prophet) — ver
[`specs/008-analytical-questions/`](specs/008-analytical-questions/).

## POC: Chat NL-to-SQL

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
- **Passo a passo completo de deploy** (para rodar sua própria instância): `specs/009-poc-app-chat/quickstart.md`

Este app substitui o Genie Space originalmente cogitado no roadmap (ver
`DECISOES_PROJETO.md` §8 e `.specify/memory/constitution.md` v1.1.2) —
decisão tomada durante o desenvolvimento porque a configuração do Genie
é exclusiva de UI, sem caminho via CLI/API, o que quebraria o padrão
deste projeto de execução ponta a ponta automatizada.
