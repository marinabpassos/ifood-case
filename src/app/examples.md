# poc-app-chat — Exemplos de Interação

> ⚠️ **POC (prova de conceito), conteúdo bônus deste case**
> — não é uma das entregas obrigatórias (features 002-008) nem um
> produto pronto para produção (ver "Limitações conhecidas da POC" em
> `specs/009-poc-app-chat/spec.md`). Este app (`src/app/`) é o
> item "Consumo" do roadmap, substituindo o Genie
> Space originalmente cogitado (ver `constitution.md` v1.1.2 e
> `specs/009-poc-app-chat/spec.md`, seção Clarifications).

Todos os exemplos abaixo foram capturados rodando o backend real do app
(`generate_sql` → `execute_sql` → `format_answer`, as mesmas funções de
`app.py`) contra o SQL Warehouse e o serving endpoint reais deste
projeto — não são respostas inventadas ou simuladas.

**App**: `poc-app-chat`
**URL**: `https://poc-app-chat-3576264130915931.aws.databricksapps.com`
**Serving endpoint**: `databricks-meta-llama-3-1-8b-instruct`

---

## Exemplo 1

**Pergunta**: Qual foi a média de total_amount em março de 2023?

**SQL gerado**:
```sql
SELECT AVG(total_amount) FROM ifood_case.silver.yellow_taxi_trips WHERE EXTRACT(MONTH FROM tpep_pickup_datetime) = 3 AND EXTRACT(YEAR FROM tpep_pickup_datetime) = 2023
```

**Resultado executado**: `avg(total_amount) = 28.289838167096057`

**Resposta formatada**: "A média de receita em março de 2023 foi de aproximadamente $28."

**Capturado em**: 2026-07-23T22:41:43Z

---

## Exemplo 2

**Pergunta**: Quantas corridas tiveram mais de 4 passageiros?

**SQL gerado**:
```sql
SELECT COUNT(*) FROM ifood_case.silver.yellow_taxi_trips WHERE passenger_count > 4
```

**Resultado executado**: `count(1) = 354748`

**Resposta formatada**: "354.748 corridas tiveram mais de 4 passageiros."

**Capturado em**: 2026-07-23T22:41:43Z

---

## Exemplo 3

**Pergunta**: Qual a hora do dia com o maior número de corridas?

**SQL gerado**:
```sql
SELECT EXTRACT(HOUR FROM tpep_pickup_datetime), COUNT(*) FROM ifood_case.silver.yellow_taxi_trips GROUP BY EXTRACT(HOUR FROM tpep_pickup_datetime) ORDER BY COUNT(*) DESC LIMIT 1
```

**Resultado executado**: `hour = 18, count(1) = 1094907`

**Resposta formatada**: "A hora do dia com o maior número de corridas é às 18 horas, com um total de 1.094.907 corridas."

**Capturado em**: 2026-07-23T22:41:43Z

---

## Exemplo 4 (pergunta de acompanhamento — demonstra resolução de contexto)

**Pergunta 1**: Qual a receita total do período?

**SQL gerado**:
```sql
SELECT SUM(total_amount) FROM ifood_case.silver.yellow_taxi_trips
```

**Resultado executado**: `sum(total_amount) = 434378880.73`

**Resposta formatada**: "A receita total do período é de $434.378.880,73."

**Pergunta 2** (acompanhamento, mesma sessão): e a média mensal e diária?

**SQL gerado** (usa a Pergunta 1/Resposta 1 como contexto para entender "a média"):
```sql
SELECT
  (SELECT AVG(total_mes) FROM (SELECT SUM(total_amount) AS total_mes FROM ifood_case.silver.yellow_taxi_trips GROUP BY date_format(tpep_pickup_datetime, 'yyyy-MM'))) AS media_mensal,
  (SELECT AVG(total_dia) FROM (SELECT SUM(total_amount) AS total_dia FROM ifood_case.silver.yellow_taxi_trips GROUP BY date(tpep_pickup_datetime))) AS media_diaria
```

**Resultado executado**: `media_mensal = 86875776.14588356, media_diaria = 2876681.329337741`

**Resposta formatada**: "A média mensal é de $86.875.776,15 e a média diária é de $2.876.681,33."

**Capturado em**: 2026-07-24T04:04:55Z

---

## Notas

- Todas as consultas leem exclusivamente `ifood_case.silver.yellow_taxi_trips`
  (FR-002, FR-007) — nenhuma escrita, nenhuma modificação de tabela.
- O Exemplo 1 confirma consistência com o resultado já publicado em
  `analysis/answers.md` (feature 008): média de `total_amount` em março
  de 2023 = 28.29 — mesmo valor, calculado de forma independente por
  este app.
- O modelo (`databricks-meta-llama-3-1-8b-instruct`) substitui
  `databricks-gpt-5-6-luna` (planejado originalmente em `research.md`
  §2) — o endpoint original tem rate limit 0 configurado neste
  workspace, descoberto rodando a chamada real durante a implementação
  (ver `tasks.md` T010).
- O Exemplo 4 foi capturado depois de um bug real encontrado pelo
  usuário em uso normal do app: sem nenhum contexto, a pergunta de
  acompanhamento "e a média mensal e diária?" gerava um SQL genérico
  (`AVG(total_amount)`, a média por corrida) e relatava o mesmo número
  como "mensal" e "diária" ao mesmo tempo -- errado nos dois sentidos.
  Corrigido passando a última troca da conversa como contexto textual
  (não é memória persistida -- cada pergunta ainda gera sua própria
  consulta SQL nova) e um exemplo concreto de agregação mensal/diária
  no prompt de geração de SQL (`research.md` §3c). No mesmo bug, a
  primeira resposta também errou a ordem de grandeza (relatou "$43,4
  milhões" para um valor real de $434.378.880,73) -- corrigido parando
  de deixar o modelo reescrever números grandes: agora o Python formata
  o valor e o modelo só copia, nunca recalcula.
