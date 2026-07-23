-- Average passenger_count by hour of day (0-23), for trips whose pickup
-- fell in May 2023, across the whole yellow-taxi fleet.
-- Answers the case brief's second analytical question.
SELECT
  hour(tpep_pickup_datetime) AS pickup_hour,
  ROUND(AVG(passenger_count), 2) AS avg_passenger_count,
  COUNT(*) AS trip_count
FROM ifood_case.silver.yellow_taxi_trips
WHERE year(tpep_pickup_datetime) = 2023
  AND month(tpep_pickup_datetime) = 5
GROUP BY hour(tpep_pickup_datetime)
ORDER BY 1;
