"""Configuración compartida de la batería de pruebas (pytest).

Añade el directorio ``backend`` al ``sys.path`` para que los módulos del
proyecto (``metricas_config``, ``models``, ``agent``, ``database``...) puedan
importarse directamente, con independencia del directorio desde el que se
lance ``pytest``.

Define además dos *fixtures* y los *markers* personalizados que clasifican
las pruebas según necesiten o no servicios externos (PostgreSQL, Ollama).
"""

import os
import sys

import pytest

# --- Rutas del proyecto -------------------------------------------------
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BACKEND_DIR, "config.yaml")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


# --- Markers personalizados --------------------------------------------
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "db: prueba que requiere una instancia de PostgreSQL en marcha.",
    )
    config.addinivalue_line(
        "markers",
        "llm: prueba que requiere el modelo LLM local (Ollama) en marcha.",
    )
    config.addinivalue_line(
        "markers",
        "integracion: prueba de integración entre dos o más componentes.",
    )


# --- Fixtures -----------------------------------------------------------
@pytest.fixture(scope="session")
def catalogo():
    """Catálogo de métricas real, cargado desde ``config.yaml``.

    Es una dependencia pura (solo PyYAML), por lo que está disponible en
    cualquier entorno sin necesidad de levantar servicios.
    """
    from metricas_config import MetricasConfig

    return MetricasConfig(CONFIG_PATH)
