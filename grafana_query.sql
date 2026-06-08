-- Query SQL para Grafana (Panel de Time Series)
-- Esta query devuelve datos de múltiples métricas correctamente separados

SELECT 
  fecha as time,
  valor as value,
  m.nombre as metric
FROM datos d
JOIN metricas m ON d.metrica_id = m.id
WHERE m.nombre IN (${metrica:sqlstring})
ORDER BY time, metric

-- IMPORTANTE: 
-- La columna 'metric' es la clave para que Grafana separe las series
-- Grafana usará automáticamente esta columna para crear líneas diferentes
