-- Average total_amount charged per month, across the whole yellow-taxi
-- fleet (all rows in the silver table, no additional filtering).
-- Answers the case brief's first analytical question.
SELECT
  date_format(tpep_pickup_datetime, 'yyyy-MM') AS month,
  ROUND(AVG(total_amount), 2) AS avg_total_amount,
  COUNT(*) AS trip_count
FROM ifood_case.silver.yellow_taxi_trips
GROUP BY date_format(tpep_pickup_datetime, 'yyyy-MM')
ORDER BY 1;
