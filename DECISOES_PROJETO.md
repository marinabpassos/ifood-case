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

## 3. Arquitetura de dados

Modelo em camadas (medalhão simplificado):

1. **Landing zone / bronze**: arquivos parquet originais, como chegaram, em
   Unity Catalog Volume (ou DBFS)
2. **Camada de consumo / silver**: tabela Delta gerenciada, com as colunas
   obrigatórias já tipadas e limpas:
   - `VendorID`
   - `passenger_count`
   - `total_amount`
   - `tpep_pickup_datetime`
   - `tpep_dropoff_datetime`
   - (demais colunas do arquivo original podem ser ignoradas)

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

- Ferramenta: skill `sdd-skill` (SpillwaveSolutions/sdd-skill) para Claude Code,
  baseada na metodologia do GitHub Spec-Kit
- Fluxo: **Specify → Plan → Tasks → Implement**, com checkpoint humano entre
  cada fase
- Specs devem viver como arquivos versionados em `.claude/specs/` dentro do
  repositório (não apenas em notebooks do workspace)
- Instalação:
  ```
  /plugin marketplace add SpillwaveSolutions/sdd-skill
  /plugin install sdd-skill
  ```
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
├─ .claude/
│  └─ specs/       # Specs versionadas do fluxo SDD
├─ README.md
└─ requirements.txt
```

## 12. Critérios de avaliação (do enunciado, para não perder de vista)

- Qualidade e organização do código
- Processo de análise exploratória
- Justificativa das escolhas técnicas
- Criatividade na solução proposta
- Clareza na comunicação dos resultados

## 13. Pendências / próximos passos

- [ ] Validar se o domínio dos parquets da NYC TLC está liberado na saída de
      internet da Free Edition
- [ ] Configurar conexão MCP do Databricks no Claude Code
- [ ] Instalar `sdd-skill` e rodar a fase **Specify** do pipeline de ingestão
- [ ] Rodar data profiling sobre os dados brutos (bronze) antes de modelar a
      silver
- [ ] Definir e aplicar regras de data quality na transição bronze → silver
- [ ] Escrever o contrato de dados da tabela silver (`contracts/`) antes de
      implementar a escrita da tabela
- [ ] Instrumentar observability da pipeline (métricas de volume, schema,
      lineage e tabela de log de execução)
- [ ] Criar Genie Space sobre a tabela silver
- [ ] Prototipar o agente custom de NL-to-SQL
