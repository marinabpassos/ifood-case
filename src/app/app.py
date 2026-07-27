"""poc-app-chat (feature 009): POC de chat NL-to-SQL sobre
ifood_case.silver.yellow_taxi_trips. Sem Genie Space em nenhum ponto
(constitution v1.1.2) -- pergunta em portugues, resposta em portugues,
gerada a partir de uma consulta SQL real executada no SQL Warehouse do
projeto. POC deste case, nao um substituto das entregas
obrigatorias (features 002-008).

ATENCAO: isto e uma POC (prova de conceito), nao um produto pronto para
producao -- ver "Limitacoes conhecidas da POC" em
specs/009-poc-app-chat/spec.md.

Serving endpoint: SERVING_ENDPOINT_NAME (via app.yaml valueFrom), setado
para databricks-meta-llama-3-1-8b-instruct -- nao databricks-gpt-5-6-luna
como planejado originalmente (research.md decisao 2), que tem rate limit
0 configurado neste workspace (erro real, descoberto rodando a chamada
de verdade durante a implementacao) e portanto nao responde a nenhuma
chamada.
"""

import os
import re
import time

import gradio as gr
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from databricks.sdk.service.sql import StatementState

WAREHOUSE_ID = os.environ["DATABRICKS_WAREHOUSE_ID"]
SERVING_ENDPOINT = os.environ["SERVING_ENDPOINT_NAME"]
TABLE = "ifood_case.silver.yellow_taxi_trips"

w = WorkspaceClient()

# Copiado de contracts/nyc_taxi_silver.yaml (features 005/006). Nao lido
# em runtime: um Databricks App nao compartilha o mount direto de
# workspace filesystem que notebooks/jobs tem, e ler via Workspace API
# exigiria permissao adicional para um schema de 5 colunas que já está
# congelado para este case -- risco desnecessário para o ganho.
SCHEMA_DESCRIPTION = """
Tabela: ifood_case.silver.yellow_taxi_trips (uma linha = uma corrida de táxi amarelo)
Colunas:
- VendorID (integer, not null): fornecedor do equipamento de despacho/medição do táxi.
- passenger_count (integer, not null, sempre > 0): número de passageiros na corrida.
- total_amount (decimal, not null, sempre > 0): valor total cobrado do passageiro (tarifa + taxas + pedágios).
- tpep_pickup_datetime (timestamp, not null): data/hora de início da corrida (sempre entre 2023-01-01 e 2023-05-31).
- tpep_dropoff_datetime (timestamp, not null): data/hora de fim da corrida (sempre após tpep_pickup_datetime).
""".strip()

SQL_SYSTEM_PROMPT = f"""Você é um gerador de SQL para o Databricks SQL.
Dada uma pergunta em português sobre a tabela abaixo, responda APENAS
com uma única instrução SQL SELECT que responde à pergunta -- nenhum
texto antes ou depois, sem markdown, sem ponto e vírgula final.

{SCHEMA_DESCRIPTION}

Regras:
- Use exclusivamente a tabela {TABLE}.
- Gere apenas SELECT -- nunca INSERT/UPDATE/DELETE/DROP/CREATE/ALTER.
- Se a mensagem do usuário incluir "Pergunta anterior" / "Resposta
  anterior", use isso APENAS para entender referências implícitas na
  pergunta atual. A query gerada deve responder sozinha, sem depender
  de nenhuma query anterior.
- "Média por mês" ou "média mensal" de uma métrica somada (ex.: receita)
  é DIFERENTE de "média por corrida" -- primeiro some a métrica agrupada
  por mês/dia, depois calcule a média desses totais. NÃO confunda com
  AVG(coluna) direto, que é a média por linha/corrida. Exemplo para
  "qual a média mensal e diária de receita?":
  SELECT
    (SELECT AVG(total_mes) FROM (SELECT SUM(total_amount) AS total_mes FROM {TABLE} GROUP BY date_format(tpep_pickup_datetime, 'yyyy-MM'))) AS media_mensal,
    (SELECT AVG(total_dia) FROM (SELECT SUM(total_amount) AS total_dia FROM {TABLE} GROUP BY date(tpep_pickup_datetime))) AS media_diaria
- Se a pergunta (mesmo com o contexto) não puder ser respondida com os
  dados desta tabela, responda exatamente: SEM_RESPOSTA
"""

ANSWER_SYSTEM_PROMPT = (
    "Você resume resultados de consulta SQL em uma resposta curta, em "
    "português, para um usuário de negócio não técnico. Responda só com "
    "a resposta final, sem repetir a pergunta e sem mencionar SQL. "
    "Os valores monetários dos dados (total_amount) estão em dólares "
    "americanos (USD) -- use o símbolo $ ou 'USD', nunca R$. "
    "IMPORTANTE: os números do resultado já vêm formatados corretamente "
    "-- copie-os EXATAMENTE como estão, sem arredondar, sem recalcular e "
    "sem converter a escala (não escreva 'milhão'/'mil' por conta "
    "própria; o número já reflete a escala real)."
)

FORBIDDEN_KEYWORDS = ("insert", "update", "delete", "drop", "create", "alter", "truncate", "merge", "grant")

FALLBACK_ANSWER = "Não consegui responder isso com os dados disponíveis."


def extract_sql(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^```(?:sql)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
    return text


def is_safe_select(sql: str) -> bool:
    normalized = sql.strip().rstrip(";").strip().lower()
    if not normalized.startswith("select"):
        return False
    return not any(re.search(rf"\b{kw}\b", normalized) for kw in FORBIDDEN_KEYWORDS)


def build_context(history) -> str:
    """Resume a última troca da conversa, como apoio para o modelo
    resolver perguntas de acompanhamento elípticas (ex.: "e a média
    mensal e diária?" depois de "qual a receita total do período?").
    Não é memória persistida -- cada pergunta ainda gera sua própria
    consulta SQL independente (FR-008); isto só ajuda a entender do que
    a pergunta atual está falando quando ela não é autocontida."""
    if not history:
        return ""
    last_turn = history[-1]
    if not isinstance(last_turn, (list, tuple)) or len(last_turn) != 2:
        return ""
    user_msg, bot_msg = last_turn
    lines = []
    if user_msg:
        lines.append(f"Pergunta anterior: {user_msg}")
    if bot_msg:
        lines.append(f"Resposta anterior: {bot_msg}")
    return "\n".join(lines)


def generate_sql(question: str, context: str = "") -> str:
    user_content = f"{context}\n\nPergunta atual: {question}" if context else question
    response = w.serving_endpoints.query(
        name=SERVING_ENDPOINT,
        messages=[
            ChatMessage(role=ChatMessageRole.SYSTEM, content=SQL_SYSTEM_PROMPT),
            ChatMessage(role=ChatMessageRole.USER, content=user_content),
        ],
        temperature=0.0,
        max_tokens=300,
    )
    return extract_sql(response.choices[0].message.content)


def execute_sql(sql: str):
    """`wait_timeout` tem teto de 50s (imposto pelo SDK); um SQL Warehouse
    frio (auto_stop_mins=10, feature 002) pode levar mais que isso para
    voltar a subir, então um statement ainda em PENDING/RUNNING é
    consultado via `get_statement` em vez de assumido como concluído --
    descoberto ao esbarrar nisso de verdade depois que o warehouse ficou
    ocioso (2026-07-24)."""
    result = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql,
        wait_timeout="50s",
    )
    deadline = time.monotonic() + 90
    while result.status.state in (StatementState.PENDING, StatementState.RUNNING):
        if time.monotonic() > deadline:
            raise TimeoutError("A consulta demorou demais para o warehouse responder.")
        time.sleep(2)
        result = w.statement_execution.get_statement(result.statement_id)
    if result.status.state != StatementState.SUCCEEDED:
        message = result.status.error.message if result.status.error else result.status.state.value
        raise RuntimeError(f"Falha ao executar SQL: {message}")
    columns = [c.name for c in result.manifest.schema.columns]
    rows = result.result.data_array or []
    return columns, rows


def format_value(value) -> str:
    """Formata números com separador de milhar '.' e decimal ',' (padrão
    BR) em Python -- não deixamos o modelo reescrever/reescalar números
    grandes em texto livre, o que se mostrou pouco confiável (um modelo
    pequeno relatou $43,4 milhões para um total real de $434,4 milhões
    em uso real, 2026-07-24)."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    formatted = f"{num:,.2f}"
    return formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def format_answer(question: str, columns: list, rows: list) -> str:
    if not rows:
        return "Não encontrei nenhum resultado para essa pergunta nos dados disponíveis."
    result_text = "\n".join(
        ", ".join(f"{c}={format_value(v)}" for c, v in zip(columns, row)) for row in rows[:50]
    )
    response = w.serving_endpoints.query(
        name=SERVING_ENDPOINT,
        messages=[
            ChatMessage(role=ChatMessageRole.SYSTEM, content=ANSWER_SYSTEM_PROMPT),
            ChatMessage(
                role=ChatMessageRole.USER,
                content=f"Pergunta: {question}\nResultado da consulta ({len(rows)} linha(s)):\n{result_text}",
            ),
        ],
        temperature=0.0,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


def responder(question: str, history) -> str:
    """Cada resposta vem de uma consulta SQL nova e independente -- não
    há estado persistido entre perguntas (FR-008). A última troca da
    conversa é passada como contexto textual só para o modelo entender
    referências implícitas em perguntas de acompanhamento."""
    question = (question or "").strip()
    if not question:
        return "Digite uma pergunta sobre as corridas de táxi amarelo."
    try:
        context = build_context(history)
        sql = generate_sql(question, context)
        if sql.strip().upper() == "SEM_RESPOSTA" or not is_safe_select(sql):
            return FALLBACK_ANSWER
        columns, rows = execute_sql(sql)
        return format_answer(question, columns, rows)
    except Exception:
        return FALLBACK_ANSWER


demo = gr.ChatInterface(
    fn=responder,
    title="poc-app-chat — iFood Case (POC)",
    description=(
        "⚠️ **POC (prova de conceito), não um produto pronto para "
        "produção** — não é uma entrega "
        "obrigatória. Faça uma pergunta em português sobre as corridas "
        "de yellow táxi (Jan-Mai 2023) e receba uma resposta gerada a "
        "partir de uma consulta SQL real, sem escrever nenhum código. "
        "Limitações conhecidas: contexto de só 1 turno anterior, modelo "
        "pequeno (8B), sem controle de custo — ver `spec.md` para a "
        "lista completa."
    ),
    examples=[
        "Qual foi a média de total_amount em março de 2023?",
        "Quantas corridas tiveram mais de 4 passageiros?",
        "Qual a hora do dia com o maior número de corridas?",
    ],
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("DATABRICKS_APP_PORT", 8000)))
