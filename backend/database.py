"""Capa de acceso a datos.

Define :class:`DatabaseService`, que encapsula el acceso a PostgreSQL:
mantiene un único ``Engine`` de SQLAlchemy (con su pool de conexiones) y
expone los métodos de consulta que utiliza el backend.
"""

from typing import Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DB_URL = "postgresql://admin:admin@localhost:5433/base_datos_v3"


class DatabaseService:
    """Servicio de acceso a la base de datos PostgreSQL.

    Centraliza la conexión: crea una sola vez el ``Engine`` (y, con él, el
    pool de conexiones) y ofrece los métodos para ejecutar consultas.
    """

    def __init__(self, db_url: str = DB_URL) -> None:
        self._engine: Engine = create_engine(db_url)

    def get_connection(self):
        """Devuelve una conexión cruda (para pandas o consultas directas)."""
        return self._engine.connect()

    def run_query(self, query_str: str, params: Optional[dict] = None) -> Any:
        """Ejecuta una consulta SQL parametrizada.

        Devuelve una lista de diccionarios (un ``dict`` por fila) o, si se
        produce un error, un ``dict`` ``{"error": ...}``. Mantiene exactamente
        el mismo comportamiento que la versión anterior basada en funciones.
        """
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query_str), params or {})
                keys = result.keys()
                return [dict(zip(keys, row)) for row in result.fetchall()]
        except Exception as exc:
            return {"error": str(exc)}


# Instancia única compartida por todo el backend (un solo Engine / pool de conexiones).
db = DatabaseService()
