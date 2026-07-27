-- Daily trip count across the full Jan-May 2023 window, across the
-- whole yellow-taxi fleet, no additional filtering beyond what the
-- silver table already guarantees.
-- Bonus/differentiator input for the Prophet trend + weekly-seasonality
-- decomposition (analysis/analise.py) -- not one of the case
-- brief's two required questions.
SELECT
  date(tpep_pickup_datetime) AS trip_date,
  COUNT(*) AS trip_count
FROM ifood_case.silver.yellow_taxi_trips
GROUP BY date(tpep_pickup_datetime)
ORDER BY 1;
