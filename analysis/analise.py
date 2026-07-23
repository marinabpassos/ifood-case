# Databricks notebook source
# MAGIC %md
# MAGIC # Análises Analíticas — iFood Case
# MAGIC
# MAGIC Notebook único: uma seção por pergunta (célula de markdown com o
# MAGIC enunciado, célula `%sql` com a query cuja tabela de resultado *é*
# MAGIC a resposta, célula Python que gera o gráfico a partir desse mesmo
# MAGIC resultado), mais uma seção final claramente rotulada como bônus.
# MAGIC Lê exclusivamente `ifood_case.silver.yellow_taxi_trips`
# MAGIC (features 004-006), sem filtragem ou limpeza adicional própria
# MAGIC desta feature. As mesmas queries também existem como arquivos
# MAGIC `.sql` standalone em `analysis/`, para quem preferir rodar sem
# MAGIC notebook.

# COMMAND ----------

# MAGIC %pip install prophet plotly "kaleido==0.2.1"

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

import base64
import json

import plotly.graph_objects as go
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly

# Paleta iFood: vermelho de marca como única cor de dado (uma série por
# gráfico -> um hue só, sem necessidade de legenda -- a série é
# identificada pelo título). Contrast-checked vs. branco: 4.46:1
# (dataviz skill, scripts/validate_palette.js `contrast()`), acima do
# piso de 3:1 para marcas.
IFOOD_RED = "#EA1D2C"
IFOOD_RED_SOFT = "rgba(234, 29, 44, 0.18)"  # tinta clara do mesmo hue, faixa de incerteza
INK = "#1A1A1A"     # texto (títulos, eixos, rótulos) -- nunca a cor do dado
MUTED = "#6B6B6B"   # ticks, textos secundários
GRID = "#E3E3E3"    # gridlines recessivas
FONT = "Helvetica Neue, Arial, sans-serif"  # pilha CSS -- Kaleido renderiza via
# Chromium headless, que faz fallback silencioso de fonte (ao contrário do
# findfont do matplotlib, que despeja um warning por lookup ausente)


def style_layout(fig, title, xaxis_title, yaxis_title, height=560):
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, font=dict(size=20, color=INK, family=FONT), x=0.02, xanchor="left"),
        font=dict(family=FONT, color=INK, size=13),
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        margin=dict(t=80, l=70, r=30, b=60),
        height=height,
        width=1000,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=True, linecolor=GRID, tickfont=dict(color=MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False, showline=False, tickfont=dict(color=MUTED))
    return fig


def fig_to_base64(fig, scale=2):
    return base64.b64encode(fig.to_image(format="png", scale=scale)).decode("ascii")


def show(fig):
    displayHTML(fig.to_html(include_plotlyjs="cdn", full_html=False))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pergunta 1 — Qual a média de valor total (`total_amount`)
# MAGIC recebido em um mês, considerando todos os yellow táxis da frota?

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   date_format(tpep_pickup_datetime, 'yyyy-MM') AS month,
# MAGIC   ROUND(AVG(total_amount), 2) AS avg_total_amount,
# MAGIC   COUNT(*) AS trip_count
# MAGIC FROM ifood_case.silver.yellow_taxi_trips
# MAGIC GROUP BY date_format(tpep_pickup_datetime, 'yyyy-MM')
# MAGIC ORDER BY 1

# COMMAND ----------

q1_pdf = _sqldf.toPandas()

q1_fig = go.Figure(go.Bar(
    x=q1_pdf["month"], y=q1_pdf["avg_total_amount"],
    marker_color=IFOOD_RED, marker_line_width=0, width=0.55,
    text=[f"${v:.2f}" for v in q1_pdf["avg_total_amount"]],
    textposition="outside", textfont=dict(color=INK, size=13, family=FONT),
    cliponaxis=False,
))
style_layout(q1_fig, "Média de total_amount por mês (Jan-Mai 2023)", "Mês", "Valor médio (USD)")
# Sem isso, o Plotly detecta "2023-01" como data e monta um eixo
# temporal contínuo (dez/2022-mai/2023) em vez de 5 categorias
# discretas -- as barras ficam finas a ponto de sumir (`width=0.55` é
# interpretado em milissegundos num eixo de data, não em unidades de
# categoria). Forçar categórico corrige.
q1_fig.update_xaxes(type="category")
q1_fig.update_yaxes(range=[0, q1_pdf["avg_total_amount"].max() * 1.2])
show(q1_fig)

q1_chart_b64 = fig_to_base64(q1_fig)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pergunta 2 — Qual a média de passageiros (`passenger_count`)
# MAGIC por cada hora do dia, considerando as corridas de maio e todos os
# MAGIC yellow táxis da frota?

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   hour(tpep_pickup_datetime) AS pickup_hour,
# MAGIC   ROUND(AVG(passenger_count), 2) AS avg_passenger_count,
# MAGIC   COUNT(*) AS trip_count
# MAGIC FROM ifood_case.silver.yellow_taxi_trips
# MAGIC WHERE year(tpep_pickup_datetime) = 2023
# MAGIC   AND month(tpep_pickup_datetime) = 5
# MAGIC GROUP BY hour(tpep_pickup_datetime)
# MAGIC ORDER BY 1

# COMMAND ----------

q2_pdf = _sqldf.toPandas()

q2_fig = go.Figure(go.Bar(
    x=q2_pdf["pickup_hour"], y=q2_pdf["avg_passenger_count"],
    marker_color=IFOOD_RED, marker_line_width=0, width=0.6,
))
style_layout(q2_fig, "Média de passageiros por hora do dia (Maio 2023)", "Hora do dia", "Média de passageiros")
q2_fig.update_xaxes(dtick=1)
q2_fig.update_yaxes(range=[0, q2_pdf["avg_passenger_count"].max() * 1.2])

# Poucos rótulos diretos (mínimo e máximo) -- rotular as 24 barras
# poluiria o gráfico (dataviz skill: "label selectively").
min_i = q2_pdf["avg_passenger_count"].idxmin()
max_i = q2_pdf["avg_passenger_count"].idxmax()
for i in (min_i, max_i):
    q2_fig.add_annotation(
        x=q2_pdf["pickup_hour"].iloc[i], y=q2_pdf["avg_passenger_count"].iloc[i],
        text=f"{q2_pdf['avg_passenger_count'].iloc[i]:.2f}",
        showarrow=False, yshift=16, font=dict(color=INK, size=13, family=FONT),
    )
show(q2_fig)

q2_chart_b64 = fig_to_base64(q2_fig)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bonus: Volume Diário de Corridas — Tendência e Sazonalidade
# MAGIC (Prophet)
# MAGIC
# MAGIC ⚠️ **Conteúdo diferencial/bonus** — não é uma das duas perguntas
# MAGIC obrigatórias do case (Perguntas 1 e 2 acima). Não deve ser
# MAGIC interpretado como substituto de nenhuma das respostas
# MAGIC obrigatórias.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   date(tpep_pickup_datetime) AS trip_date,
# MAGIC   COUNT(*) AS trip_count
# MAGIC FROM ifood_case.silver.yellow_taxi_trips
# MAGIC GROUP BY date(tpep_pickup_datetime)
# MAGIC ORDER BY 1

# COMMAND ----------

daily_pdf = _sqldf.toPandas()
daily_pdf = daily_pdf.rename(columns={"trip_date": "ds", "trip_count": "y"})
daily_pdf["ds"] = daily_pdf["ds"].astype(str)

model = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=False)
model.fit(daily_pdf)
forecast = model.predict(daily_pdf[["ds"]])

# `plot_plotly` desenha, nessa ordem: [0] pontos observados (markers,
# pretos); [1] linha invisível do limite superior da faixa de incerteza;
# [2] "Predicted" -- a linha visível de ajuste, que TAMBÉM carrega o
# preenchimento da metade superior da faixa (fill='tonexty' contra [1]);
# [3] linha invisível do limite inferior, preenchendo a metade inferior
# da faixa contra [2] (fill='tonexty'). Confirmado inspecionando
# fig.data em uma execução de sondagem antes de escrever este estilo --
# reaproveita os artistas que a biblioteca já desenha (não reimplementa
# o plot), só troca cor/texto.
trend_fig = plot_plotly(model, forecast)
trend_fig.data[0].marker.color = INK
trend_fig.data[0].marker.size = 5
trend_fig.data[0].marker.opacity = 0.55
trend_fig.data[2].line.color = IFOOD_RED
trend_fig.data[2].line.width = 2.5
trend_fig.data[2].fillcolor = IFOOD_RED_SOFT
trend_fig.data[3].fillcolor = IFOOD_RED_SOFT
style_layout(trend_fig, "BÔNUS: Volume diário de corridas — ajuste + tendência (Prophet)",
             "Data", "Número de corridas", height=560)
# plot_plotly() liga por padrão um range-slider + botões de intervalo
# (1w/1m/6m/1y/all) -- fazem sentido num notebook interativo, mas viram
# ruído morto numa imagem estática exportada.
trend_fig.update_xaxes(rangeslider_visible=False, rangeselector=None)
show(trend_fig)

daily_trend_chart_b64 = fig_to_base64(trend_fig)

# COMMAND ----------

# `plot_components_plotly` desenha 1 linha por subplot (tendência,
# sazonalidade semanal), sem pontos observados e sem faixa de incerteza
# nessa configuração -- confirmado na mesma sondagem. O eixo x da
# sazonalidade semanal é uma semana de referência fixa do Prophet
# (2017-01-01 domingo a 2017-01-07 sábado) num eixo de datas comum, sem
# rótulos de dia da semana pré-definidos -- por isso o `ticktext` abaixo
# é setado explicitamente, na mesma ordem dessas datas de referência.
components_fig = plot_components_plotly(model, forecast)
components_fig.data[0].line.color = IFOOD_RED
components_fig.data[0].line.width = 2.5
components_fig.data[1].line.color = IFOOD_RED
components_fig.data[1].line.width = 2.5

components_fig.update_layout(
    template="plotly_white",
    title=dict(text="BÔNUS: Volume diário de corridas — tendência e sazonalidade semanal",
               font=dict(size=18, color=INK, family=FONT), x=0.02, xanchor="left"),
    font=dict(family=FONT, color=INK, size=13),
    plot_bgcolor="white", paper_bgcolor="white", showlegend=False,
    margin=dict(t=90, l=70, r=30, b=60), height=650, width=1000,
)
components_fig.update_xaxes(showgrid=False, zeroline=False, showline=True, linecolor=GRID, tickfont=dict(color=MUTED))
components_fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickfont=dict(color=MUTED))
components_fig.update_yaxes(title_text="Tendência (corridas/dia)", row=1, col=1)
components_fig.update_yaxes(title_text="Efeito semanal (corridas)", row=2, col=1)
components_fig.update_xaxes(
    title_text="Dia da semana", row=2, col=1, tickmode="array",
    tickvals=["2017-01-01", "2017-01-02", "2017-01-03", "2017-01-04",
              "2017-01-05", "2017-01-06", "2017-01-07"],
    ticktext=["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"],
)
show(components_fig)

daily_components_chart_b64 = fig_to_base64(components_fig)

daily_rows = daily_pdf.rename(columns={"ds": "trip_date", "y": "trip_count"}).to_dict(orient="records")

# COMMAND ----------

result = {
    "q1_rows": q1_pdf.to_dict(orient="records"),
    "q1_chart_png_base64": q1_chart_b64,
    "q2_rows": q2_pdf.to_dict(orient="records"),
    "q2_chart_png_base64": q2_chart_b64,
    "daily_rows": daily_rows,
    "daily_trend_chart_png_base64": daily_trend_chart_b64,
    "daily_components_chart_png_base64": daily_components_chart_b64,
}
print(json.dumps({k: v for k, v in result.items() if not k.endswith("_base64")}))
try:
    dbutils.notebook.exit(json.dumps(result))
except NameError:
    pass
