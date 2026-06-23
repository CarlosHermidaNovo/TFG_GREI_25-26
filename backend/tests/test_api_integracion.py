"""Pruebas de INTEGRACIÓN extremo a extremo de la API (FastAPI).

Ejercitan el contrato HTTP completo: ``POST /chat`` -> ``AgentService`` ->
herramienta -> respuesta JSON (HU-01..HU-11). Validan los modelos Pydantic
de entrada/salida (ChatRequest / ChatResponse) y el patrón PASSTHROUGH del
agente.

Requieren PostgreSQL **y** el LLM local (Ollama con qwen2.5). Se marcan con
``db`` y ``llm`` y se omiten si el entorno no está disponible.

Ejecución:
    pytest -m "integracion"          # incluirlas
    pytest -m "not llm"              # excluir lo que requiere modelo
"""

import pytest

pytestmark = [pytest.mark.integracion, pytest.mark.db, pytest.mark.llm]

# Dependencias del entorno completo.
fastapi_testclient = pytest.importorskip("fastapi.testclient")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient

    try:
        from main import app
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"No se pudo cargar la app FastAPI: {exc}")
    return TestClient(app)


# =====================================================================
# Salud del servicio (no requiere LLM, pero se agrupa aquí por cohesión)
# =====================================================================
def test_healthcheck(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# =====================================================================
# Contrato de /chat — validación Pydantic
# =====================================================================
def test_chat_rechaza_cuerpo_invalido(client):
    """Falta el campo obligatorio 'texto' -> 422 Unprocessable Entity."""
    resp = client.post("/chat", json={"mensaje": "hola"})
    assert resp.status_code == 422


def test_chat_visualizacion_devuelve_url(client):
    """HU-01 extremo a extremo: 'muéstrame el pib' -> URL de Grafana."""
    resp = client.post("/chat", json={"texto": "muéstrame el pib"})
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert "respuesta" in cuerpo
    assert "var-metrica=" in cuerpo["respuesta"]


def test_chat_listar_metricas(client):
    """HU-04: '¿qué datos tienes?' -> lista de métricas."""
    resp = client.post("/chat", json={"texto": "¿qué datos tienes?"})
    assert resp.status_code == 200
    assert "Métricas disponibles" in resp.json()["respuesta"]


def test_chat_descripcion(client):
    """HU-11: '¿qué es el pib?' -> descripción + unidad."""
    resp = client.post("/chat", json={"texto": "¿qué es el pib?"})
    assert resp.status_code == 200
    r = resp.json()["respuesta"]
    assert "Unidad de medida" in r or "Descripción" in r
