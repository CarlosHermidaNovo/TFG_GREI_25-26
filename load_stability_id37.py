import pandas as pd
from sqlalchemy import create_engine, text
import os
import re

# --- CONFIGURACIÓN ---
DB_URL = 'postgresql://admin:admin@localhost:5433/base_datos_v3'

engine = create_engine(DB_URL)

def limpiar_valor(valor):
    """Convierte '<2.5' en 2.5 y maneja errores."""
    if isinstance(valor, (int, float)):
        return valor
    valor = str(valor).replace('<', '').replace('>', '').replace(',', '.')
    try:
        return float(valor)
    except:
        return None

def limpiar_fecha(anio):
    """Convierte '2014-2016' o '20142016' en '2014-01-01'."""
    anio_str = str(anio)
    # Buscar los primeros 4 dígitos consecutivos
    match = re.search(r'(\d{4})', anio_str)
    if match:
        return f"{match.group(1)}-01-01"
    return None

def procesar_archivos_estabilidad():
    archivos = [
        r'data\Espanha_estabilidad_politica.csv',
        r'data\Alemania_estabilidad_politica.csv',
        r'data\Italia_estabilidad_politica.csv'
    ]
    
    fixed_id = 37

    for ruta_csv in archivos:
        if not os.path.exists(ruta_csv):
            print(f"❌ El archivo {ruta_csv} no existe. Saltando...")
            continue

        nombre_archivo = os.path.basename(ruta_csv)
        
        if nombre_archivo.startswith('Espanha_'):
            pais = 'España'
        elif nombre_archivo.startswith('Alemania_'):
            pais = 'Alemania'
        elif nombre_archivo.startswith('Italia_'):
            pais = 'Italia'
        else:
            pais = 'Desconocido'

        print(f"📂 Procesando: {nombre_archivo} con ID fijo = 37 (País: {pais})...")
        
        try:
            # 1. Leer CSV
            df = pd.read_csv(ruta_csv, encoding='utf-8')
            
            # Normalizar nombres de columnas
            df.columns = [c.strip().replace('\ufeff', '') for c in df.columns]
            
            # Verificar columnas necesarias
            cols_necesarias = ['Producto', 'Elemento', 'Año', 'Unidad', 'Valor']
            if not all(col in df.columns for col in cols_necesarias):
                print(f"   ⚠️ Error: {nombre_archivo} no tiene formato estándar FAO.")
                continue

            # Tomamos el primer registro para definir la métrica
            first_row = df.iloc[0]
            producto = first_row['Producto']
            elemento = first_row['Elemento']
            unidad = first_row['Unidad']
            
            nombre_metrica = f"{producto} - {elemento}"
            categoria = "estabilidad_politica"

            with engine.connect() as conn:
                # A. Insertar o Actualizar Métrica con ID 37 (sobreescribe la info en el primer paso)
                conn.execute(text("""
                    INSERT INTO metricas (id, nombre, unidad, categoria) 
                    VALUES (:id, :nom, :uni, :cat) 
                    ON CONFLICT (id) DO UPDATE 
                    SET nombre = EXCLUDED.nombre, 
                        unidad = EXCLUDED.unidad, 
                        categoria = EXCLUDED.categoria;
                """), {"id": fixed_id, "nom": nombre_metrica, "uni": unidad, "cat": categoria})
                conn.commit()
                
                # Borrar datos ÚNICAMENTE de ese país para esta métrica (para no pisar a Italia/Alemania)
                conn.execute(text("DELETE FROM datos WHERE metrica_id = :id AND pais = :pais"), 
                             {"id": fixed_id, "pais": pais})
                conn.commit()

                # B. Preparar datos
                data_to_insert = []
                for _, row in df.iterrows():
                    if row['Producto'] != producto or row['Elemento'] != elemento:
                        continue

                    fecha_limpia = limpiar_fecha(row['Año'])
                    valor_limpio = limpiar_valor(row['Valor'])
                    
                    if fecha_limpia and valor_limpio is not None:
                        data_to_insert.append({
                            "metrica_id": fixed_id,
                            "fecha": fecha_limpia,
                            "valor": valor_limpio,
                            "pais": pais
                        })
                
                # C. Insertar datos
                if data_to_insert:
                    conn.execute(text("""
                        INSERT INTO datos (metrica_id, fecha, valor, pais)
                        VALUES (:metrica_id, :fecha, :valor, :pais)
                    """), data_to_insert)
                    conn.commit()
                    print(f"   ✨ Insertados {len(data_to_insert)} registros de {pais} en métrica {fixed_id}.")
                else:
                    print("   ⚠️ No se encontraron datos válidos para insertar.")

        except Exception as e:
            print(f"   ❌ Error crítico en {nombre_archivo}: {e}")

if __name__ == "__main__":
    procesar_archivos_estabilidad()
