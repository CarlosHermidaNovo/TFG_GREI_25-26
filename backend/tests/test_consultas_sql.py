"""Pruebas de INTEGRACIÓN de la herramienta de consulta numérica.

Comprueban la cadena ``consultar_datos_sql`` -> ``DatabaseService`` ->
PostgreSQL (HU-03, HU-07). Requieren la base de datos en marcha, por lo que
se marcan con ``@pytest.mark.db`` y se OMITEN automáticamente si la conexión
no está disponible.

Ejecución selectiva:
    pytest -m db            # solo estas pruebas
    pytest -m "not db"      # excluirlas (entorno sin BD)
"""

import pytest

agent = pytest.importorskip("agent", reason="Requiere el entorno del backend.")


@pytest.fixture(scope="module")
def hay_bd():
    """Verifica que PostgreSQL responde; si no, omite el módulo."""
    from database import db

    res = db.run_query("SELECT 1 AS ok")
    if isinstance(res, dict) and "error" in res:
        pytest.skip(f"PostgreSQL no disponible: {res['error']}")
    return True


pytestmark = pytest.mark.db


def _llamar(tool, **kwargs):
    return tool.invoke(kwargs)


def test_promedio_obesidad_incluye_unidad_y_contexto(hay_bd):
    """HU-03 + HU-07: la respuesta numérica debe traer unidad e insight."""
    r = _llamar(agent.consultar_datos_sql, pregunta="¿cuál es el promedio de obesidad?")
    assert "promedio" in r.lower()
    assert "%" in r                  # unidad de la obesidad
    assert "Contexto:" in r          # insight de config.yaml (HU-07)


def test_maximo_pib_devuelve_anio(hay_bd):
    r = _llamar(agent.consultar_datos_sql, pregunta="dame el máximo del pib")
    assert "máximo" in r.lower()
    # El formato es "...en el año YYYY."
    assert "año" in r.lower()


def test_tendencia_indica_direccion(hay_bd):
    r = _llamar(agent.consultar_datos_sql, pregunta="¿ha aumentado la población rural?")
    assert any(p in r.lower() for p in ["aumentado", "disminuido", "mantenido"])


def test_valor_en_anio_concreto(hay_bd):
    r = _llamar(agent.consultar_datos_sql, pregunta="pib en 2018")
    assert "2018" in r


def test_metrica_no_identificada(hay_bd):
    r = _llamar(agent.consultar_datos_sql, pregunta="¿cuál es el promedio de zzzz?")
    assert "no pude identificar" in r.lower()
