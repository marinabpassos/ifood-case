# iFood Data Architect Case — Roteiro de Apresentação

Conteúdo pronto para gerar um deck (~15 slides, PT-BR) com qualquer ferramenta
de slides. Ênfase: **engenharia de dados agêntica / Spec-Driven Development
(SDD)** — a metodologia como fio condutor, com a pipeline medallion como o
artefato que ela produziu.

## Restrições de conteúdo (do próprio projeto — respeitar)

- O app de chat é **sempre POC**, nunca "diferencial" (constitution v1.1.4, DECISOES §8).
- **Não há camada Gold / star schema** — foi descartada de propósito. Não inventar.
- Números corretos: **16.186.386 linhas, 0 duplicatas** no bronze; 5 arquivos
  mensais (NYC Yellow Taxi, Jan–Mai 2023).

---

## Slide 1 — Capa
**iFood Data Architect Case — Engenharia de Dados Agêntica**
- NYC Yellow Taxi · Jan–Mai 2023
- Databricks (Free Edition) · PySpark + Delta Lake + Unity Catalog
- Desenvolvido com Spec-Driven Development + Claude Code

## Slide 2 — O desafio (duplo objetivo)
- **Objetivo técnico:** ingerir corridas de táxi de NY, disponibilizar via SQL
  e responder a 2 perguntas analíticas.
- **Meta-objetivo:** servir de exemplo de boas práticas de **engenharia de
  dados agêntica** usando Claude Code como ferramenta de desenvolvimento.
- Critérios de avaliação: qualidade/organização do código, processo de EDA,
  justificativa das escolhas, criatividade, clareza na comunicação.

## Slide 3 — Metodologia: Spec-Driven Development (SDD)
- Fluxo: **Constitution → Specify → [Clarify] → Plan → [Checklist] → Tasks →
  [Analyze] → Implement → Converge**.
- **Checkpoints humanos** entre as fases — o agente não avança sozinho.
- Ferramentas: GitHub Spec Kit + Claude Code.
- Cada arquivo de código cita os FRs e as decisões de `research.md` que implementa.

## Slide 4 — A Constituição do projeto
Princípios que governaram todas as decisões:
- **Qualidade de dados é um gate, não um relatório** (não-negociável).
- **Contratos de dados antes do código.**
- **Observabilidade é entregável**, não opcional.
- **Stack fixa** (PySpark, Delta, Unity Catalog).
- **Mínimo layering** — sem abstração especulativa.

## Slide 5 — 9 features, 9 ciclos SDD
Cada feature = um ciclo SDD completo (spec/plan/tasks/implement):
- 001 Scaffold do repositório
- 002 Ambiente & Landing Zone
- 003 Data Profiling (EDA)
- 004 Camada Bronze
- 005 Contrato de dados da Silver
- 006 Data Quality & Camada Silver
- 007 Observabilidade da pipeline
- 008 Perguntas analíticas
- 009 POC App de chat

## Slide 6 — Arquitetura Medallion
- Três camadas distintas, cada uma em seu schema no catalog `ifood_case`:
  **Landing → Bronze → Silver**.
- Decisão explícita por **3 camadas** (não 2).
- **Sem camada Gold:** as 2 perguntas são agregações diretas sobre a silver;
  não há dimensões reais a modelar. Adicionar um star schema violaria o
  princípio de mínimo layering.

## Slide 7 — Landing & Bronze
- **Landing:** 5 parquets baixados byte-a-byte da fonte NYC TLC; verificação de
  cada arquivo (não vazio, legível pelo Spark, sem outlier de tamanho,
  Content-Length batendo). Nenhuma transformação.
- **Bronze:** ingestão 1:1, **sem regras de negócio** — só tratamento técnico
  (cast de drift de schema entre meses, metadados de ingestão, dedup de linhas
  100% idênticas).
- Resultado: **16.186.386 linhas · 0 duplicatas**.

## Slide 8 — Profiling / EDA como gate
- Roda **antes** de qualquer transformação de negócio.
- Mede volumetria por mês, schema real vs esperado, nulos e distribuições.
- Princípio central: **"as regras não são arbitrárias — cada uma sai de um
  achado do profiling."**

## Slide 9 — Contrato de dados + Data Quality
- `contracts/nyc_taxi_silver.yaml` escrito **antes** do código de escrita.
- Schema validado **antes** de gravar a silver (o job falha em caso de drift).
- **4 regras de qualidade (todas `drop`, justificadas):**
  1. `total_amount` ≤ 0 (não é tarifa real)
  2. `passenger_count` nulo ou zero (defeito de registro)
  3. `dropoff` anterior ao `pickup` (duração negativa)
  4. datas fora da janela Jan–Mai 2023 (vazamento de mês adjacente)

## Slide 10 — Observabilidade
- Cada run (bronze e silver) registra uma linha em `ifood_case.silver._pipeline_run_log`:
  linhas lidas/escritas, drops por regra, status, duração.
- **Alerta** quando qualquer regra derruba **>1%** das linhas.
- Lineage nativo do Unity Catalog: landing → bronze → silver.

## Slide 11 — Perguntas analíticas
**Q1 — Média de `total_amount` por mês (frota inteira):**
- Tendência de alta: $27,46 (jan) → $29,45 (mai), com pequena queda em fev.

**Q2 — Média de `passenger_count` por hora do dia (maio):**
- Baixa variância (1,26–1,46 passageiros/corrida); menor às 6h, maior às 2h.
- Sem picos de corridas multi-passageiro em horas específicas.

## Slide 12 — Bônus: decomposição com Prophet
- Volume diário de corridas: tendência de **~92k → ~107k corridas/dia** no período.
- **Sazonalidade semanal** clara: mínimos dom/seg (−13 a −15k abaixo da tendência),
  pico na quinta (~+10,6k).

## Slide 13 — POC: Chat NL→SQL
- Databricks App (Gradio, interface em PT): pergunta em linguagem natural →
  SQL gerado por Foundation Model → execução real na silver → resposta formatada.
- **É uma POC, não um produto** — com guarda contra SQL injection (só SELECT).
- Substituiu o Genie Space planejado: Genie é só-UI, sem caminho via CLI/API, o
  que quebraria o padrão de automação ponta-a-ponta do projeto.

## Slide 14 — Engenharia agêntica na prática
Limitações reais encontradas e contornadas (talking points concretos):
- Sem `ALTER SCHEMA ... RENAME` no Unity Catalog → rename via create-copy-verify-drop.
- `input_file_name()` não suportado em compute UC → uso de `_metadata.file_name`.
- Endpoint de serving com rate limit → fallback de modelo.
- SQL Warehouse frio → lógica de polling.
- `DECISOES_PROJETO.md` como memória/log de decisões do projeto.

## Slide 15 — Fechamento
- Entregue: pipeline medallion completo + 2 respostas analíticas + bônus + POC de consumo.
- O que a abordagem **agêntica / SDD** trouxe: rastreabilidade FR→código,
  contratos versionados, qualidade como gate e checkpoints humanos em cada fase.
