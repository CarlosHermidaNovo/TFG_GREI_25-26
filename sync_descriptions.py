import yaml
import os
from sqlalchemy import create_engine, text

#-----CONFIGURACIÓN-----
DB_URL = 'postgresql://admin:admin@localhost:5433/base_datos_v3'
# Ruta del archivo config.yaml
PATH_CONFIG = os.path.join('backend', 'config.yaml')

#-----FUNCIONES-----
def sync_descriptions():
    print("Conectando a la base de datos...")
    try:
        engine = create_engine(DB_URL)
        connection = engine.connect()
        print("Conectado a la base de datos.")
    except Exception as e:
        print(f"Error contectando a la BD: {e}")
        return
    

    #Verificar si existe el archivo YAML
    if not os.path.exists(PATH_CONFIG):
        print(f"El archivo {PATH_CONFIG} no se encuentra.")
        print("Verifique la ruta del archivo. Debe de encontrarse dentro de la carpeta 'backend'.")
        return

    print(f"Leyendo el archivo {PATH_CONFIG}...")
    with open(PATH_CONFIG, 'r', encoding='utf-8') as f:
        try:
            config_data=yaml.safe_load(f)
            print("Archivo leído correctamente.")
        except yaml.YAMLError as e:
            print(f"Error al leer el archivo YAML: {e}")
            return
    
    datasets = config_data.get('datasets',[])
    print(f"Se encontraron {len(datasets)} datasets en el archivo YAML.")

    actualizados = 0
    no_encontrados = 0

    with connection as conn:
        for ds in datasets:
            nombre_metrica = ds.get('nombre')
            descripcion = ds.get('descripcion')
            insights = ds.get('insights')

            # Combinamos descripcion + insights para tener toda la info de la BD
            # Usamos saltos de línea para conservar el orden

            texto_final = f"{descripcion}"
            if insights:
                texto_final += f"\n\nInsights: {insights}"

            if nombre_metrica and descripcion:
                #Ejecutar UPDATE
                query = text("""
                    UPDATE metricas
                    SET descripcion = :desc
                    WHERE nombre = :nom
                    """)
                
                result = conn.execute (query, {"desc": texto_final, "nom": nombre_metrica})

                if result.rowcount > 0:
                    print(f"Actualizado: {nombre_metrica[:40]}...")
                    actualizados += 1
                else:
                    print(f"No existe en BD: {nombre_metrica} (Revisa el nombre en YAML)")
                    no_encontrados += 1
        conn.commit()

    print("\n" + "="*40)
    print(f"RESUMEN:")
    print(f"Actualizados: {actualizados}")
    print(f"No encontrados: {no_encontrados}")
    print("="*40 + "\n")


if __name__ == "__main__":
    try:
        import yaml
        sync_descriptions()
    except ImportError:
        print("Falta la librerýa 'PyYAML'.")
        print("Instalación: pip install pyyaml")
