from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuración
DB_URL = 'postgresql://admin:admin@localhost:5433/base_datos_v3'

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_connection():
    """Devuelve una conexión cruda para usar con pandas o queries directas."""
    return engine.connect()

def run_query(query_str: str, params: dict = None):
    """Ejecuta una query SQL cruda y devuelve los resultados como lista de dicts."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query_str), params or {})
            # Convertir a lista de diccionarios
            keys = result.keys()
            return [dict(zip(keys, row)) for row in result.fetchall()]
    except Exception as e:
        return {"error": str(e)}
