"""Pruebas unitarias del catalogo de metricas (``MetricasConfig.buscar``).

Cubren el nucleo del reconocimiento de lenguaje natural del sistema: la
resolucion de una metrica a partir del texto del usuario mediante los tres
pasos (alias exacto, palabras clave en el nombre y *fuzzy matching*) y la
tolerancia lexica exigida por HU-05.

Son pruebas PURAS: solo dependen de PyYAML, por lo que se ejecutan sin
levantar PostgreSQL ni Ollama.
"""

import pytest

# Nombres canonicos usados como oraculo en las aserciones.
PIB = "PIB per cápita, PPA ($ a precios internacionales constantes de 2021) - Valor"
OBESIDAD = "Prevalencia de la obesidad entre la población adulta (18 años y más) - Valor"
RURAL = "Población-Estimaciones - Población rural"
CEREALES = "Cereales, primarios - Producción"
ESTABILIDAD = "Estabilidad política y ausencia de violencia o terrorismo (índice) - Valor"


# =====================================================================
# 1. PASO 1 - Coincidencia por ALIAS exacto  (consultas cortas)
# =====================================================================
@pytest.mark.parametrize(
    "consulta, esperado",
    [
        ("PIB", PIB),
        ("pib", PIB),                      # insensible a mayusculas
        ("Producto Interior Bruto", PIB),  # alias multipalabra
        ("Tasa de Obesidad", OBESIDAD),
        ("España vaciada", RURAL),         # alias coloquial
        ("Producción de Cereales", CEREALES),
    ],
)
def test_alias_exacto(catalogo, consulta, esperado):
    m = catalogo.buscar(consulta)
    assert m is not None
    assert m.nombre == esperado


# =====================================================================
# 2. PASO 1 - Alias DENTRO de una frase  (alias_en_texto=True)
# =====================================================================
@pytest.mark.parametrize(
    "frase, esperado",
    [
        ("¿cuál es el promedio de obesidad en españa?", OBESIDAD),
        ("dame el máximo del pib", PIB),
        ("ha aumentado la poblacion rural?", RURAL),
    ],
)
def test_alias_dentro_de_frase(catalogo, frase, esperado):
    # Reproduce la llamada que hace consultar_datos_sql.
    m = catalogo.buscar(frase, alias_en_texto=True, min_long=3, min_coincidencias=2)
    assert m is not None
    assert m.nombre == esperado


# =====================================================================
# 3. PASO 2 - Palabras clave contenidas en el NOMBRE tecnico
# =====================================================================
@pytest.mark.parametrize(
    "consulta, esperado",
    [
        ("estabilidad politica", ESTABILIDAD),
        ("prevalencia obesidad adulta", OBESIDAD),
    ],
)
def test_palabras_clave(catalogo, consulta, esperado):
    m = catalogo.buscar(consulta)
    assert m is not None
    assert m.nombre == esperado


# =====================================================================
# 4. PASO 3 - Fuzzy matching: tolerancia a erratas (HU-05)
# =====================================================================
@pytest.mark.parametrize(
    "consulta_con_errata, esperado",
    [
        ("obsidad", OBESIDAD),     # letra omitida
        ("oblsidad", OBESIDAD),    # letra intercambiada
    ],
)
def test_fuzzy_matching_erratas(catalogo, consulta_con_errata, esperado):
    m = catalogo.buscar(consulta_con_errata)
    assert m is not None, f"No se reconocio la errata '{consulta_con_errata}'"
    assert m.nombre == esperado


@pytest.mark.xfail(
    reason="LIMITACION DETECTADA: con cutoff=0.4, la errata 'cerelaes' se "
    "resuelve por similitud a 'Densidad de lineas de ferrocarril' en lugar de "
    "a 'Cereales'. Documentado en el capitulo de Pruebas como mejora futura.",
    strict=True,
)
def test_fuzzy_errata_cereales_limitacion(catalogo):
    m = catalogo.buscar("cerelaes")
    assert m is not None and m.nombre == CEREALES


# =====================================================================
# 5. Tolerancia lexica: ausencia de tildes (HU-05)
# =====================================================================
@pytest.mark.parametrize(
    "sin_tilde, esperado",
    [
        ("poblacion rural", RURAL),
        ("riqueza per capita", PIB),
    ],
)
def test_tolerancia_sin_tildes(catalogo, sin_tilde, esperado):
    m = catalogo.buscar(sin_tilde)
    assert m is not None
    assert m.nombre == esperado


# =====================================================================
# 6. Casos NEGATIVOS - entradas que NO deben resolver una metrica
# =====================================================================
@pytest.mark.parametrize(
    "consulta_invalida",
    [
        "xyzqwerty",              # texto sin relacion, sin similitud
        "asdfgh",                 # texto aleatorio
    ],
)
def test_consulta_invalida_devuelve_none(catalogo, consulta_invalida):
    assert catalogo.buscar(consulta_invalida) is None


@pytest.mark.xfail(
    reason="LIMITACION DETECTADA: una cadena vacia satisface 'texto in alias' "
    "en el paso 1 y devuelve la primera metrica del catalogo. Deberia "
    "rechazarse. Documentado en el capitulo de Pruebas.",
    strict=True,
)
def test_cadena_vacia_deberia_ser_none(catalogo):
    assert catalogo.buscar("") is None


@pytest.mark.xfail(
    reason="LIMITACION DETECTADA: una consulta fuera de dominio ('dime un "
    "chiste') no se rechaza; el fuzzy con cutoff=0.4 la asocia a una metrica. "
    "Documentado en el capitulo de Pruebas como falso positivo del NLU.",
    strict=True,
)
def test_consulta_fuera_de_dominio_deberia_ser_none(catalogo):
    assert catalogo.buscar("dime un chiste") is None


# =====================================================================
# 7. Integridad del catalogo cargado desde config.yaml
# =====================================================================
def test_catalogo_carga_todas_las_metricas(catalogo):
    nombres = catalogo.listar_nombres()
    # config.yaml define 23 datasets.
    assert len(nombres) == 23
    # No debe haber nombres duplicados (restriccion UNIQUE en la BD).
    assert len(nombres) == len(set(nombres))


def test_todas_las_metricas_tienen_alias_y_unidad(catalogo):
    for m in catalogo.metricas:
        assert m.alias, f"La metrica '{m.nombre}' no tiene alias definidos."
        assert m.unidad, f"La metrica '{m.nombre}' no tiene unidad definida."
