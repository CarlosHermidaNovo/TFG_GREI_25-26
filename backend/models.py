"""Clases de dominio del sistema."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Metrica:
    """Indicador agroalimentario del catálogo.

    Representa una entrada del catálogo semántico definido en ``config.yaml``.
    El atributo ``categoria`` se almacena en la tabla ``metricas`` de PostgreSQL
    (lo asigna el ETL a partir del fichero de origen) y por eso aquí es
    opcional: no aparece en ``config.yaml``.
    """

    nombre: str
    alias: List[str] = field(default_factory=list)
    unidad: str = ""
    descripcion: str = ""
    insights: str = ""
    categoria: Optional[str] = None
