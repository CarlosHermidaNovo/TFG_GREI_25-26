"""Pruebas unitarias del pipeline ETL (``etl_loader``).

Validan las dos funciones de transformación que dan robustez a la ingesta
frente a los formatos "sucios" de la FAO (HU implícita de calidad de datos
y objetivo de ETL del Capítulo 1):

* ``limpiar_valor``: normaliza valores acotados (``<2.5``) y separadores
  decimales, y descarta basura.
* ``limpiar_fecha``: convierte los rangos plurianuales de la FAO
  (``2014-2016``) en una fecha única normalizada a 1 de enero.

El módulo ``etl_loader`` crea un ``Engine`` de SQLAlchemy al importarse, pero
NO abre conexión hasta ejecutar una consulta, por lo que estas pruebas no
requieren PostgreSQL.
"""

import os
import sys

import pytest

# etl_loader.py vive en la raíz del proyecto, no en backend/.
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

etl = pytest.importorskip("etl_loader")  # se omite si falta SQLAlchemy/pandas


# =====================================================================
# limpiar_valor  — valores correctos
# =====================================================================
@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("<2.5", 2.5),      # valor acotado de la FAO
        (">100", 100.0),    # cota superior
        ("1,5", 1.5),       # separador decimal europeo
        ("42", 42.0),       # entero como texto
        (3.14, 3.14),       # ya es float
        (10, 10),           # ya es int
    ],
)
def test_limpiar_valor_correcto(entrada, esperado):
    assert etl.limpiar_valor(entrada) == esperado


# =====================================================================
# limpiar_valor  — valores incorrectos -> None
# =====================================================================
@pytest.mark.parametrize("basura", ["N/A", "sin dato", "", "abc"])
def test_limpiar_valor_invalido_devuelve_none(basura):
    assert etl.limpiar_valor(basura) is None


# =====================================================================
# limpiar_fecha  — rangos y años sueltos
# =====================================================================
@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("2014-2016", "2014-01-01"),  # rango plurianual -> primer año
        ("20142016", "2014-01-01"),   # rango sin guion
        ("2020", "2020-01-01"),       # año suelto
        (2018, "2018-01-01"),         # año numérico
    ],
)
def test_limpiar_fecha_correcta(entrada, esperado):
    assert etl.limpiar_fecha(entrada) == esperado


@pytest.mark.parametrize("sin_anio", ["texto", "", "abc-def"])
def test_limpiar_fecha_sin_anio_devuelve_none(sin_anio):
    assert etl.limpiar_fecha(sin_anio) is None
