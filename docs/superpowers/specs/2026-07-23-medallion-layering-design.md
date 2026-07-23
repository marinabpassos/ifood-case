# Design: Camadas de Modelagem (Landing → Bronze → Silver)

**Data**: 2026-07-23
**Status**: Aprovado
**Contexto**: Brainstorming feito antes de iniciar a feature 004, a partir de
uma pergunta sobre modelagem de dados — a landing zone deveria ser uma
camada separada da bronze? Vale uma camada gold com star schema?

## Problema

A constituição do projeto (v1.0.0) tinha uma inconsistência interna:

- Princípio VI descrevia a arquitetura mínima como **landing/bronze
  fundidos → silver** (2 camadas físicas).
- Princípio III já falava em lineage nativa do Unity Catalog cobrindo
  **volume→bronze→silver** (3 estágios), tratando bronze como algo distinto
  do volume de landing.

Na prática, hoje só existe o Volume `ifood_case.bronze.yellow_taxi_raw`
(arquivos parquet crus, feature 002) — nenhuma tabela bronze foi criada; o
profiling (feature 003) leu direto do Volume. A pergunta que motivou esta
sessão: isso deveria continuar assim, ou vale criar uma tabela bronze
física, separada da landing zone? E depois da silver, vale uma camada
gold/star schema?

## Decisão

Três camadas físicas, resolvendo a inconsistência a favor do modelo de 3
camadas (o que a Principle III já implicava):

```
Landing (Volume, parquet cru)  →  Bronze (Delta)  →  Silver (Delta)
```

### Landing

- Já existe (feature 002). Volume de Unity Catalog com os 5 arquivos
  parquet originais, imutáveis, um por mês (Jan–Mai 2023).
- **Ação pendente de infra**: o schema que hoje contém esse volume se chama
  `ifood_case.bronze` — precisa ser renomeado para `ifood_case.landing` para
  não colidir com o novo schema `bronze` (a tabela Delta). Isso é trabalho
  da feature 004, não desta sessão de design (CLI do Databricks não
  disponível nesta sessão de brainstorming).

### Bronze

- Tabela Delta nova: `ifood_case.bronze.yellow_taxi_trips`.
- Ingestão 1:1 da landing, com:
  - Cast de schema consistente entre os 5 meses — resolve o caso concreto
    achado no profiling (`passenger_count`: `float` em 2023-01, `integer`
    nos demais meses; mesmo padrão em `ratecodeid`, não obrigatória).
  - Colunas técnicas de ingestão: `_source_file`, `_ingested_at`.
  - Dedup de linhas 100% idênticas (full-row duplicates) — checagem
    técnica, sem julgamento de negócio. (Nota: o profiling não achou
    nenhuma duplicata full-row em nenhum dos 5 meses — a regra existe por
    completude/defesa, não porque resolve um problema conhecido nesse
    dataset.)
- **Não faz**: nenhuma regra de qualidade de negócio (não filtra
  `total_amount` negativo/zero, `passenger_count` nulo/zero, datas fora do
  range, ou `dropoff < pickup`). Bronze é "o mesmo dado, em Delta, com
  schema consistente" — não um pré-filtro de qualidade.

### Silver

- Tabela Delta: `ifood_case.silver.yellow_taxi_trips`. Lida a partir da
  bronze (não mais direto da landing/parquet).
- Aplica as regras de qualidade de negócio identificadas no profiling
  (`specs/003-data-profiling/findings.md`), formalizadas no contrato
  `contracts/nyc_taxi_silver.yaml` (feature 005):
  - `passenger_count` nulo ou zero
  - `total_amount` negativo ou zero
  - `tpep_dropoff_datetime` anterior a `tpep_pickup_datetime`
  - Datas fora do intervalo Jan–Mai 2023
- Grão: uma linha = uma corrida.
- Colunas obrigatórias: `VendorID`, `passenger_count`, `total_amount`,
  `tpep_pickup_datetime`, `tpep_dropoff_datetime`.

### Sem camada gold / star schema

Descartado deliberadamente. As duas perguntas analíticas do case são
agregações diretas sobre a silver:

1. Média de `total_amount` por mês — `GROUP BY` mês.
2. Média de `passenger_count` por hora do dia em maio — `GROUP BY HOUR(tpep_pickup_datetime)`.

Nenhuma das duas se beneficia de dimensões separadas (data/hora/vendor):
`VendorID` tem poucos valores fixos e não é uma dimensão com atributos
próprios a modelar; não há coluna de localização entre as colunas
obrigatórias. Um star schema aqui adicionaria tabelas e código de pipeline
sem servir a nenhum requisito concreto — contrário ao Princípio VI da
constituição (mínimo de camadas necessário, sem abstração especulativa).

## Impacto no roadmap

Nova feature **004 — Camada Bronze**, inserida antes do que era a feature
004 (Contrato da Silver). Demais features renumeradas. Ver
`DECISOES_PROJETO.md` §13 para a tabela completa atualizada.

| # | Feature | Depende de |
|---|---|---|
| 004 | Camada Bronze (renomear schema landing + criar tabela bronze) | 003 |
| 005 | Contrato de Dados da Silver | 004 |
| 006 | Data Quality & Camada Silver (lê da bronze) | 005 |
| 007 | Observability da Pipeline | 006 |
| 008 | Análises Analíticas | 006 |
| 009 | Consumo & Diferencial | 006 |

## Documentos alterados nesta sessão

- `.specify/memory/constitution.md`: v1.0.0 → v1.1.0 (Princípios III e VI
  reescritos para refletir 3 camadas; Sync Impact Report no topo do
  arquivo).
- `DECISOES_PROJETO.md`: seção 3 (arquitetura de dados) e seção 13
  (roadmap) atualizadas.
- Este arquivo (novo).

## Próximo passo

Rodar `/speckit-specify` para a feature 004 (Camada Bronze), cobrindo:
renomear `ifood_case.bronze` → `ifood_case.landing` no Unity Catalog, e
criar/popular `ifood_case.bronze.yellow_taxi_trips` conforme definido acima.
