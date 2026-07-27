-- Média de total_amount cobrado por mês, considerando toda a frota de
-- yellow táxi (todas as linhas da tabela silver, sem filtragem adicional).
-- Responde à primeira pergunta analítica do enunciado do case.
SELECT
  date_format(tpep_pickup_datetime, 'yyyy-MM') AS month,
  ROUND(AVG(total_amount), 2) AS avg_total_amount,
  COUNT(*) AS trip_count
FROM ifood_case.silver.yellow_taxi_trips
GROUP BY date_format(tpep_pickup_datetime, 'yyyy-MM')
ORDER BY 1;
