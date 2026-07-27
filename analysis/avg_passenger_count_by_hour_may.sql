-- Média de passenger_count por hora do dia (0-23), para corridas cujo
-- embarque ocorreu em maio de 2023, considerando toda a frota de yellow táxi.
-- Responde à segunda pergunta analítica do enunciado do case.
SELECT
  hour(tpep_pickup_datetime) AS pickup_hour,
  ROUND(AVG(passenger_count), 2) AS avg_passenger_count,
  COUNT(*) AS trip_count
FROM ifood_case.silver.yellow_taxi_trips
WHERE year(tpep_pickup_datetime) = 2023
  AND month(tpep_pickup_datetime) = 5
GROUP BY hour(tpep_pickup_datetime)
ORDER BY 1;
