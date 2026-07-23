# Case Técnico Data Architect - iFood — Decisões de Projeto

> Este documento consolida as decisões já tomadas antes de iniciar o desenvolvimento.
> Objetivo: servir como contexto inicial para o Claude Code, alimentando a fase de
> **Specify** do fluxo de Spec-Driven Development (SDD).

## 1. Objetivo do case

Construir uma solução de engenharia de dados que:
- Ingira dados de corridas de táxi de NY (Yellow Taxi) referentes a Jan-Mai 2023
- Disponibilize os dados para consumo via SQL
- Responda a duas perguntas analíticas específicas
- Sirva como exemplo de **boas práticas de engenharia de dados agêntica**, usando
  Claude Code como ferramenta de desenvolvimento

## 2. Ambiente e infraestrutura

- **Plataforma**: Databricks **Free Edition** (sucessora da Community Edition,
  descontinuada em 2025)
- **Motivo da escolha**: gratuito, suficiente para o escopo do case, com Unity
  Catalog nativo e SQL Warehouse incluso
- **Restrições conhecidas da Free Edition** (documentar no README como
  justificativa técnica):
  - Apenas compute serverless (sem clusters customizados)
  - Saída de internet restrita a domínios confiáveis — os arquivos parquet da
    NYC TLC (`https://d37ci6vzurychx.cloudfront.net/...`) podem não estar
    liberados. **Validar isso antes de desenhar a ingestão em torno de download
    direto via notebook.** Plano B: baixar localmente e subir via Databricks
    CLI/API para a landing zone.
  - Um único SQL Warehouse, tamanho 2X-Small
  - Dados persistem mesmo com compute desligado por excesso de cota; risco real
    é apenas conta ficar deletada por **inatividade prolongada** — reabrir o
    workspace de vez em quando até a apresentação do case

### 2.1 Validação de conectividade de rede (feature 002, 2026-07-22)

- **Resultado**: **acessível diretamente** (`reachable: true`, HTTP 200) ao
  domínio `d37ci6vzurychx.cloudfront.net` (NYC TLC CloudFront), testado a
  partir de dentro do workspace (não da máquina local).
- **Método**: notebook `network_check.py` (`src/ingestion/network_check.py`)
  importado para `/Workspace/Users/marinabpassos@gmail.com/ifood_case/` e
  executado via `databricks jobs submit` (job one-off, compute serverless
  padrão da Free Edition) — não via cluster local nem download na máquina
  do case author. Uma única requisição representativa (mês 2023-01) foi
  usada para validar o domínio inteiro, já que a política de rede da Free
  Edition é aplicada por domínio, não por arquivo (spec 002, FR-001).
- **Decisão**: usar o caminho de ingestão **direto** (download via notebook
  dentro do workspace) para os 5 meses — o plano B (download local +
  upload via CLI) descrito acima **não foi necessário**.

### 2.2 Provisionamento do catalog/schema/volume (feature 002, 2026-07-22)

- **Restrição encontrada**: `databricks catalogs create ifood_case` via CLI
  falhou com "Metastore storage root URL does not exist" — a Free Edition
  usa o modelo de Default Storage e a chamada REST direta exige uma
  managed location explícita para criar um catalog novo.
- **Como foi resolvida**: `CREATE CATALOG IF NOT EXISTS ifood_case` via
  Spark SQL, executado dentro de um notebook/job (não da CLI local),
  funcionou sem exigir location explícita — o runtime do notebook resolve
  a Default Storage automaticamente. Resultado: o catalog dedicado
  `ifood_case` (não o catalog `workspace` de fallback) pôde ser usado como
  planejado.
- **Landing zone final**: `ifood_case.bronze.yellow_taxi_raw` →
  `/Volumes/ifood_case/bronze/yellow_taxi_raw/`, criado por
  `src/ingestion/landing_zone.py` e confirmado listável via
  `databricks volumes list ifood_case bronze`.
- **Nota**: uma tentativa inicial via CLI (`databricks schemas/volumes
  create` sob o catalog `workspace`) criou uma localização paralela
  (`workspace.ifood_case_bronze.yellow_taxi_raw`) antes de se descobrir o
  caminho acima — essa localização foi removida (`databricks volumes/
  schemas delete`) para não deixar ambiguidade sobre qual é "a" landing
  zone (spec 002, FR-003).

### 2.3 Landing dos 5 arquivos mensais (feature 002, 2026-07-22)

- **Resultado**: os 5 meses (Jan-Mai/2023) foram baixados diretamente do
  NYC TLC CloudFront para `/Volumes/ifood_case/bronze/yellow_taxi_raw/`
  via `src/ingestion/land_files.py`, executado como job em compute
  serverless. Todos os 5 meses passaram na verificação (`verified`) já na
  primeira tentativa — a lógica de retry (FR-008) não precisou ser
  acionada.
- **Verificação (FR-005/SC-002/SC-004)**: cada arquivo teve tamanho não
  vazio, leitura via Spark bem-sucedida (smoke-read), e nenhum foi
  outlier de tamanho (todos entre ~47MB e ~59MB, bem dentro da tolerância
  de 50% em relação à mediana dos outros meses). O tamanho de cada
  arquivo landado bate **byte a byte** com o `Content-Length` HTTP da
  fonte original — confirma que nenhuma transformação ocorreu (SC-004):

  | Mês | Tamanho (bytes) | Status |
  |---|---|---|
  | 2023-01 | 47.673.370 | verified |
  | 2023-02 | 47.748.012 | verified |
  | 2023-03 | 56.127.762 | verified |
  | 2023-04 | 54.222.699 | verified |
  | 2023-05 | 58.654.627 | verified |

- **Nenhuma restrição adicional da Free Edition** foi encontrada durante o
  download/landing além das já registradas em 2.1/2.2.

## 3. Arquitetura de dados

Modelo em camadas (medalhão simplificado), definido/revisado na sessão de
brainstorming de 2026-07-23 (ver
`docs/superpowers/specs/2026-07-23-medallion-layering-design.md`):

1. **Landing**: arquivos parquet originais, como chegaram, em Unity Catalog
   Volume — `ifood_case.landing.yellow_taxi_raw` (renomeado do schema
   `bronze` original, feature 002; a tabela em si não muda, só o
   catalog/schema que a contém)
2. **Bronze**: tabela Delta gerenciada (`ifood_case.bronze.yellow_taxi_trips`),
   ingestão 1:1 da landing — cast de schema consistente (ex.: `passenger_count`
   float/int entre meses, achado no profiling), colunas técnicas de ingestão
   (`_source_file`, `_ingested_at`), e dedup de linhas 100% idênticas. **Sem**
   regra de negócio — isso fica todo na silver.
3. **Silver**: tabela Delta gerenciada (`ifood_case.silver.yellow_taxi_trips`),
   lida a partir da bronze (não mais direto da landing), com as regras de
   qualidade de negócio aplicadas e as colunas obrigatórias já tipadas e
   limpas:
   - `VendorID`
   - `passenger_count`
   - `total_amount`
   - `tpep_pickup_datetime`
   - `tpep_dropoff_datetime`
   - (demais colunas do arquivo original podem ser ignoradas)

**Sem camada gold/star schema**: as duas perguntas analíticas (seção 4) são
agregações diretas sobre a silver; não há dimensões reais a modelar nesse
escopo. Considerado e descartado — ver design doc acima.

**Tecnologias fixadas:**
- Processamento: **PySpark** (obrigatório pelo case)
- Formato de tabela: **Delta Lake**
- Metadados/catálogo: **Unity Catalog** (nativo da Free Edition)
- Consumo final: **SQL** via Databricks SQL Warehouse

## 4. Perguntas analíticas a responder

1. Qual a média de valor total (`total_amount`) recebido em um mês,
   considerando todos os yellow táxis da frota?
2. Qual a média de passageiros (`passenger_count`) por cada hora do dia que
   pegaram táxi no mês de maio, considerando todos os táxis da frota?

Entregar como SQL ou PySpark estruturado em `analysis/`.

## 5. Data Profiling e Data Quality

Etapa obrigatória entre a landing zone (bronze) e a camada de consumo (silver) —
não pular direto para a modelagem.

**Data Profiling (análise exploratória sobre o dado bruto):**
- Volumetria por mês/arquivo (contagem de linhas, tamanho)
- Schema real dos arquivos vs. schema esperado (colunas podem variar entre
  meses nos dados da NYC TLC — checar antes de assumir consistência)
- Distribuição e nulos das colunas obrigatórias (`VendorID`,
  `passenger_count`, `total_amount`, `tpep_pickup_datetime`,
  `tpep_dropoff_datetime`)
- Estatísticas descritivas (min/max/média/percentis) de `total_amount` e
  `passenger_count` — para identificar outliers antes das análises finais

**Data Quality (regras a validar e aplicar na transição bronze → silver):**
- `total_amount` negativo ou zerado (ocorre nos dados reais da NYC TLC —
  decidir e documentar: descartar, sinalizar ou manter conforme regra de
  negócio)
- `passenger_count` nulo ou zero
- `tpep_dropoff_datetime` anterior a `tpep_pickup_datetime` (corrida com
  duração negativa)
- Datas fora do intervalo esperado (Jan-Mai 2023) — arquivos da NYC TLC
  historicamente têm registros de meses adjacentes "vazando"
- Duplicidade de registros

**Ferramentas sugeridas:**
- PySpark puro (`.describe()`, `.summary()`, agregações) para profiling básico
- Considerar `ydata-profiling` ou similar para um relatório de profiling mais
  visual, se o tempo permitir
- Documentar as regras de qualidade aplicadas e o volume de registros
  afetado/removido em cada uma — isso vira evidência concreta de "justificativa
  das escolhas técnicas" no README

## 6. Contratos de Dados das Tabelas

Definir um contrato formal para cada tabela da camada de consumo (silver),
versionado junto com o código — não apenas o schema implícito do Delta.

**O que cada contrato deve conter:**
- Nome da tabela, schema/catálogo, owner
- Schema explícito: nome da coluna, tipo, nullable ou não, descrição de negócio
- Chave primária/grão da tabela (ex.: uma linha = uma corrida)
- Regras de qualidade esperadas (ligar com a seção 5 — ex.: `total_amount` não
  deve ser negativo, `passenger_count` não nulo)
- SLA/frequência de atualização (mesmo que aqui seja uma carga única
  Jan-Mai/2023, documentar como se fosse recorrente — reforça maturidade da
  solução)
- Versionamento do contrato (ex.: `v1`) e política de breaking change (ex.:
  remoção de coluna exige nova versão)

**Onde e como registrar:**
- Arquivo declarativo versionado no repo, ex.: `contracts/nyc_taxi_silver.yaml`
  (formato inspirado no [Data Contract Specification](https://datacontract.com)
  ou algo mais simples, próprio, se preferir menos overhead)
- Complementar com **comentários de coluna no Unity Catalog**
  (`COMMENT ON COLUMN ...`), já que isso é o que aparece nativamente para quem
  consome via Genie/SQL Warehouse — o contrato declarativo é a fonte de
  verdade versionada, o comentário no catálogo é a "publicação" dele
- Validar o contrato como parte do pipeline (ex.: assert de schema antes de
  escrever na tabela silver) — não deixar como documentação solta

## 7. Observability da pipeline

Não tratar como item de "nice to have" — documentar como parte da entrega,
já que reforça "qualidade e organização do código" e "clareza na comunicação
dos resultados".

**O que instrumentar:**
- **Métricas de volume**: linhas lidas na bronze, linhas escritas na silver,
  linhas descartadas/sinalizadas por cada regra de data quality (liga direto
  com a seção 5) — logar por execução, não só o resultado final
- **Métricas de schema**: alerta se o schema real do arquivo de origem
  divergir do contrato de dados (seção 6) antes de escrever na silver
- **Lineage**: aproveitar o lineage nativo do Unity Catalog
  (`INFORMATION_SCHEMA` / lineage graph) entre volume de origem → bronze →
  silver, em vez de construir isso do zero
- **Logs de execução**: duração da ingestão, status (sucesso/falha/parcial),
  timestamp — mesmo que a carga aqui seja pontual (Jan-Mai/2023), estruturar
  como se fosse recorrente
- **Alerting mínimo**: notificação (mesmo que só um log estruturado ou
  print destacado no notebook) quando uma regra de quality descartar acima de
  um threshold definido (ex.: >1% das linhas)

**Onde registrar:**
- Uma tabela própria de metadados de execução (ex.: `_pipeline_run_log`) na
  camada de consumo, gravada a cada rodada — dá para consultar via SQL/Genie
  igual aos dados de negócio, o que é um bom diferencial de "criatividade"
- Se usar Databricks Jobs/Workflows para orquestrar, aproveitar o histórico de
  execução nativo em vez de duplicar tudo manualmente

## 8. Agente de consulta em linguagem natural (diferencial do case)

Duas frentes, com papéis diferentes:

- **Genie Space (produção)**: configurado sobre a tabela silver via UI do
  Databricks. Funciona na Free Edition. É a solução "oficial" entregue ao
  usuário final — governada pelo Unity Catalog, sem necessidade de código.
- **Agente custom (diferencial/criatividade)**: construído com Claude Code +
  MCP do Databricks, recebendo pergunta em NL, convertendo para SQL via LLM,
  executando no SQL Warehouse e retornando resposta formatada. Documentar como
  experimento de "agente de dados", não como substituto do Genie.

## 9. Metodologia de desenvolvimento: SDD (Spec-Driven Development)

- Ferramenta: **GitHub Spec Kit** nativo (`speckit-*`), instalado como skills
  do Claude Code em `.claude/skills/` — não o plugin `sdd-skill`
  (SpillwaveSolutions) cogitado inicialmente
- Fluxo: **Constitution → Specify → [Clarify] → Plan → [Checklist] → Tasks →
  [Analyze] → Implement → Converge**, com checkpoint humano entre cada fase
  (ver `ORDEM_SPECKIT.txt` para a ordem completa dos comandos)
- Specs devem viver como arquivos versionados em `specs/<NNN-nome>/` na raiz
  do repositório (convenção nativa do Spec Kit), não apenas em notebooks do
  workspace
- Constituição do projeto (princípios e governança) em
  `.specify/memory/constitution.md`
- **Cuidado**: manter o `CLAUDE.md` enxuto. Instruções nesse arquivo são
  seguidas de forma probabilística, não determinística — arquivos muito longos
  degradam a qualidade de adesão às regras. Preferir mover regras críticas para
  hooks/skills quando possível.

## 10. Ferramentas de desenvolvimento

- **Editor/agente**: Claude Code
- **Versionamento**: GitHub (repositório público ou privado)
- **MCP**: Databricks MCP (managed servers para Unity Catalog) conectado ao
  Claude Code, permitindo criar catálogo/schema, rodar SQL e inspecionar
  tabelas diretamente pelo agente

## 11. Estrutura de repositório (definida pelo case)

```
ifood-case/
├─ src/            # Código fonte da solução
├─ analysis/       # Scripts/Notebooks com as respostas das perguntas
├─ contracts/       # Contratos de dados das tabelas
├─ data/           # Landing zone local (plano B de ingestão), ignorada pelo git
├─ specs/          # Specs versionadas do fluxo SDD (convenção Spec Kit)
├─ .specify/       # Constituição, templates e config do Spec Kit
├─ README.md
└─ requirements.txt
```

## 12. Critérios de avaliação (do enunciado, para não perder de vista)

- Qualidade e organização do código
- Processo de análise exploratória
- Justificativa das escolhas técnicas
- Criatividade na solução proposta
- Clareza na comunicação dos resultados

## 13. Roadmap de features (Spec Kit)

O restante do case (além do scaffold, já entregue em `specs/001-repo-scaffold/`)
é quebrado nas features abaixo, cada uma com seu próprio ciclo
Specify → Plan → Tasks → Implement. Tamanho pensado para caber em uma spec
cada: nem tão grande a ponto de misturar contextos técnicos muito
diferentes (ex.: EDA junto com engenharia de contrato), nem tão pequena a
ponto de ser só uma task isolada.

| # | Feature | Escopo | Depende de |
|---|---|---|---|
| 002 | Ambiente & Landing Zone | Validar Free Edition (rede, serverless, warehouse), criar catalog/schema/volume no Unity Catalog, carregar os parquets Jan-Mai/2023 na landing zone | — |
| 003 | Data Profiling (EDA sobre Landing) | Volumetria por mês/arquivo, schema real vs. esperado, nulos e distribuição das colunas obrigatórias, estatísticas descritivas de `total_amount`/`passenger_count` | 002 |
| 004 | Camada Bronze | Renomear o schema `ifood_case.bronze` (feature 002) para `ifood_case.landing`; criar `ifood_case.bronze.yellow_taxi_trips` (Delta): ingestão 1:1, cast de schema, colunas técnicas de ingestão, dedup de linhas idênticas — sem regra de negócio | 003 |
| 005 | Contrato de Dados da Silver | `contracts/nyc_taxi_silver.yaml` (schema, grão, regras de qualidade, SLA, versionamento) escrito **antes** do código de escrita da tabela (Constituição, Princípio II) | 004 |
| 006 | Data Quality & Camada Silver | Aplica as regras de DQ definidas no profiling + o contrato (schema assert) sobre a bronze, escreve a tabela Delta silver tipada e limpa | 005 |
| 007 | Observability da Pipeline | Tabela `_pipeline_run_log`, métricas de volume/schema por execução, lineage nativo do Unity Catalog (landing→bronze→silver), alerting por threshold | 006 |
| 008 | Análises Analíticas | SQL/PySpark em `analysis/` respondendo as duas perguntas do case (média de `total_amount` por mês; média de `passenger_count` por hora em maio) | 006 |
| 009 | Consumo & Diferencial | Genie Space (UI, produção) sobre a silver + protótipo do agente NL-to-SQL custom via Claude Code + MCP Databricks | 006 |

**Ordem sugerida**: 002 → 003 → 004 → 005 → 006, depois 007 e 008 podem
correr em paralelo (ambas dependem só de 006), 009 por último (ou a qualquer
momento após 006, se o tempo permitir adiantar o diferencial).

Pendência solta, fora do fluxo de features (fazer antes de iniciar a 002):
- [ ] Configurar conexão MCP do Databricks no Claude Code
