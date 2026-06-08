from backend.database import run_query

# Verificar qué métricas de población existen
print("=== MÉTRICAS DE POBLACIÓN EN LA BD ===")
result = run_query("""
    SELECT m.nombre, COUNT(*) as total_registros
    FROM datos d
    JOIN metricas m ON d.metrica_id = m.id
    WHERE m.nombre LIKE '%Población%'
    GROUP BY m.nombre
""")
for r in result:
    print(f"{r['nombre']}: {r['total_registros']} registros")

# Verificar datos de población rural
print("\n=== DATOS DE POBLACIÓN RURAL ===")
result_rural = run_query("""
    SELECT TO_CHAR(fecha, 'YYYY') as año, valor
    FROM datos d
    JOIN metricas m ON d.metrica_id = m.id
    WHERE m.nombre = 'Población-Estimaciones - Población rural'
    ORDER BY fecha
    LIMIT 5
""")
print("Primeros 5 registros:")
for r in result_rural:
    print(f"  {r['año']}: {r['valor']}")

# Verificar datos de población urbana
print("\n=== DATOS DE POBLACIÓN URBANA ===")
result_urbana = run_query("""
    SELECT TO_CHAR(fecha, 'YYYY') as año, valor
    FROM datos d
    JOIN metricas m ON d.metrica_id = m.id
    WHERE m.nombre = 'Población-Estimaciones - Población urbana'
    ORDER BY fecha
    LIMIT 5
""")
print("Primeros 5 registros:")
for r in result_urbana:
    print(f"  {r['año']}: {r['valor']}")
