"""Pruebas unitarias de la generación de URLs de Grafana y rutas.

Verifican las herramientas de VISUALIZACIÓN del agente (HU-01, HU-02, HU-09,
HU-06): que la URL generada apunte al dashboard correcto, codifique la
métrica y añada un parámetro ``var-pais`` por cada país solicitado.

Importan el módulo ``agent`` real. Como ``agent`` depende de LangChain/Ollama
en tiempo de importación, si esas librerías no están instaladas el módulo de
pruebas se OMITE (skip) en lugar de fallar: así la batería sigue siendo
ejecutable en entornos ligeros (p. ej. CI sin GPU).
"""

import urllib.parse

import pytest

# Si falta el entorno del agente (LangChain/Ollama), se omite el módulo entero.
agent = pytest.importorskip(
    "agent",
    reason="Requiere el entorno del backend (LangChain + Ollama instalados).",
)

DASHBOARD_UID = "adj4dk7"
BASE = f"http://localhost:3000/d/{DASHBOARD_UID}/visor-actualizable"


def _llamar(tool, **kwargs):
    """Invoca una @tool de LangChain con argumentos de palabra clave."""
    return tool.invoke(kwargs)


# =====================================================================
# HU-01 — Visualizar una métrica individual
# =====================================================================
def test_buscar_y_graficar_pib():
    url = _llamar(agent.buscar_y_graficar, query="pib")
    assert url.startswith(BASE)
    assert "var-metrica=" in url
    assert "&kiosk" in url
    # Por defecto, España.
    assert f"var-pais={urllib.parse.quote('España')}" in url


def test_buscar_y_graficar_metrica_inexistente():
    url = _llamar(agent.buscar_y_graficar, query="zzz_no_existe_zzz")
    assert "No encontré esa métrica" in url


# =====================================================================
# HU-02 — Comparar varias métricas (multiples var-metrica)
# =====================================================================
def test_comparar_metricas_dos_indicadores():
    url = _llamar(agent.comparar_metricas, metricas="poblacion rural y poblacion urbana")
    assert url.count("var-metrica=") == 2


def test_comparar_metricas_una_sola_no_duplica():
    url = _llamar(agent.comparar_metricas, metricas="pib")
    assert url.count("var-metrica=") == 1


# =====================================================================
# HU-09 — Comparar una métrica entre varios países
# =====================================================================
def test_comparar_paises_genera_un_var_pais_por_pais():
    url = _llamar(agent.comparar_paises, metrica="pib", paises="España y Alemania")
    assert url.count("var-pais=") == 2
    assert url.count("var-metrica=") == 1
    assert urllib.parse.quote("España") in url
    assert "Alemania" in url


def test_comparar_paises_sin_paises_pide_pais():
    msg = _llamar(agent.comparar_paises, metrica="pib", paises="")
    assert "indica al menos un país" in msg.lower()


# =====================================================================
# HU-06 — Navegación al dashboard principal (ROUTE)
# =====================================================================
def test_ir_al_dashboard_devuelve_ruta():
    msg = _llamar(agent.ir_al_dashboard_principal, paises="")
    assert "ROUTE: /" in msg


# =====================================================================
# Detección de países conocidos en texto libre
# =====================================================================
def test_extraer_paises_de_texto():
    # Función auxiliar a nivel de módulo (nombre con doble guion bajo, sin
    # mangling fuera de una clase). Se accede con getattr.
    fn = getattr(agent, "__extraer_paises_de_texto")
    encontrados = fn("compara el pib entre españa y alemania")
    assert "España" in encontrados and "Alemania" in encontrados
