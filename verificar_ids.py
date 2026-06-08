from backend.database import run_query

# Verificar IDs de métricas
print("=== IDs DE MÉTRICAS ===")
result = run_query("""
    SELECT id, nombre
    FROM metricas
    WHERE nombre LIKE '%Población%'
    ORDER BY id
""")
for r in result:
    print(f"ID {r['id']}: {r['nombre']}")

# Verificar datos asociados a cada ID
print("\n=== DATOS DEL ID 11 (debería ser RURAL) ===")
result_11 = run_query("""
    SELECT TO_CHAR(fecha, 'YYYY') as año, valor
    FROM datos
    WHERE metrica_id = 11
    ORDER BY fecha
    LIMIT 5
""")
for r in result_11:
    print(f"  {r['año']}: {r['valor']}")

print("\n=== DATOS DEL ID 12 (debería ser URBANA) ===")
result_12 = run_query("""
    SELECT TO_CHAR(fecha, 'YYYY') as año, valor
    FROM datos
    WHERE metrica_id = 12
    ORDER BY fecha
    LIMIT 5
""")
for r in result_12:
    print(f"  {r['año']}: {r['valor']}")

print("\n=== COMPARACIÓN ===")
print("Rural debería tener ~9,000-10,000")
print("Urbana debería tener ~29,000-36,000")
