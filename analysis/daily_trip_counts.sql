-- Contagem diária de corridas em toda a janela Jan-Mai 2023,
-- considerando toda a frota de yellow táxi, sem filtragem adicional além
-- do que a tabela silver já garante.
-- Insumo do bônus/diferencial para a decomposição de tendência +
-- sazonalidade semanal via Prophet (analysis/analise.py) -- não é uma das
-- duas perguntas obrigatórias do enunciado do case.
SELECT
  date(tpep_pickup_datetime) AS trip_date,
  COUNT(*) AS trip_count
FROM ifood_case.silver.yellow_taxi_trips
GROUP BY date(tpep_pickup_datetime)
ORDER BY 1;
