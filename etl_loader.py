import pandas as pd
from sqlalchemy import create_engine, text
import os
import re

# --- CONFIGURACIÓN ---
DB_URL = 'postgresql://admin:admin@localhost:5433/base_datos_v3'

engine = create_engine(DB_URL)

def init_db():
    """Reinicia las tablas para empezar limpio."""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS datos CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS metricas CASCADE;"))
        
        conn.execute(text("""
            CREATE TABLE metricas (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(255) UNIQUE NOT NULL, -- Ej: "Cereales - Producción"
                unidad VARCHAR(50),
                categoria VARCHAR(100),
                descripcion TEXT
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE datos (
                id SERIAL PRIMARY KEY,
                metrica_id INT REFERENCES metricas(id),
                fecha DATE,
                valor FLOAT,
                pais VARCHAR(50) DEFAULT 'España'
            );
        """))
        conn.execute(text("CREATE INDEX idx_metrica_fecha ON datos(metrica_id, fecha);"))
        conn.commit()
    print("✅ Base de datos reiniciada y lista.")

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

def procesar_archivo(ruta_csv):
    nombre_archivo = os.path.basename(ruta_csv)
    print(f"📂 Procesando: {nombre_archivo}...")
    
    if nombre_archivo.startswith('Espanha_'):
        pais_actual = 'España'
        prefix = 'Espanha_'
    elif nombre_archivo.startswith('Alemania_'):
        pais_actual = 'Alemania'
        prefix = 'Alemania_'
    elif nombre_archivo.startswith('Italia_'):
        pais_actual = 'Italia'
        prefix = 'Italia_'
    else:
        pais_actual = 'Otro'
        prefix = ''
        
    categoria_fichero = nombre_archivo.replace('.csv', '')
    if prefix:
        categoria_fichero = categoria_fichero.replace(prefix, '')
    
    try:
        # 1. Leer CSV (detectando separador automáticamente si es posible, o asumiendo coma)
        df = pd.read_csv(ruta_csv, encoding='utf-8')
        
        # Normalizar nombres de columnas (quitar espacios, acentos raros, BOM)
        df.columns = [c.strip().replace('\ufeff', '') for c in df.columns]
        
        # Verificar que existan las columnas clave (FAO Standard)
        cols_necesarias = ['Producto', 'Elemento', 'Año', 'Unidad', 'Valor']
        if not all(col in df.columns for col in cols_necesarias):
            print(f"   ⚠️ Saltando {nombre_archivo}: No tiene formato estándar FAO.")
            return

        # 2. Iterar sobre grupos únicos de Producto + Elemento
        # Esto separa "Cereales - Producción" de "Cereales - Área"
        grupos = df.groupby(['Producto', 'Elemento', 'Unidad'])
        
        registros_totales = 0
        
        with engine.connect() as conn:
            for (producto, elemento, unidad), grupo in grupos:
                
                # A. Construir nombre único de métrica
                nombre_metrica = f"{producto} - {elemento}"
                categoria = categoria_fichero
                
                # B. Insertar Métrica en DB
                conn.execute(text("""
                    INSERT INTO metricas (nombre, unidad, categoria) 
                    VALUES (:nom, :uni, :cat) 
                    ON CONFLICT (nombre) DO NOTHING
                """), {"nom": nombre_metrica, "uni": unidad, "cat": categoria})
                conn.commit()
                
                # Obtener ID
                res = conn.execute(text("SELECT id FROM metricas WHERE nombre = :nom"), {"nom": nombre_metrica})
                metrica_id = res.fetchone()[0]
                
                # C. Preparar datos para inserción masiva
                data_to_insert = []
                for _, row in grupo.iterrows():
                    fecha_limpia = limpiar_fecha(row['Año'])
                    valor_limpio = limpiar_valor(row['Valor'])
                    
                    if fecha_limpia and valor_limpio is not None:
                        data_to_insert.append({
                            "metrica_id": metrica_id,
                            "fecha": fecha_limpia,
                            "valor": valor_limpio,
                            "pais": pais_actual
                        })
                
                # D. Insertar bloque de datos
                if data_to_insert:
                    conn.execute(text("""
                        INSERT INTO datos (metrica_id, fecha, valor, pais)
                        VALUES (:metrica_id, :fecha, :valor, :pais)
                    """), data_to_insert)
                    conn.commit()
                    registros_totales += len(data_to_insert)

        print(f"   ✨ Insertados {registros_totales} registros.")

    except Exception as e:
        print(f"   ❌ Error crítico en {nombre_archivo}: {e}")

# ==========================================
#              EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    # init_db() # ⚠️ COMENTADO PARA NO BORRAR LAS TABLAS NI ALTERAR SUS IDs 
    
    # Carpeta donde están tus csv
    carpeta_data = 'data' 
    
    # Recorrer todos los archivos CSV en la carpeta
    if os.path.exists(carpeta_data):
        archivos = [f for f in os.listdir(carpeta_data) if f.endswith('.csv')]
        for f in archivos:
            # Evitamos España para no generar registros duplicados, 
            # asumiendo que España ya se encuentra en la Base de Datos.
            if f.startswith('Alemania_') or f.startswith('Italia_'):
                procesar_archivo(os.path.join(carpeta_data, f))
    else:
        print(f"❌ La carpeta '{carpeta_data}' no existe. Créala y mete tus CSVs dentro.")