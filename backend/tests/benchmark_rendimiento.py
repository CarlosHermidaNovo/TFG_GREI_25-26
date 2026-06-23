"""Banco de pruebas de RENDIMIENTO del agente conversacional.

Mide dos magnitudes para cada tipo de intención (visualización, consulta
numérica, descripción, predicción...):

* **Latencia**: tiempo de pared (*wall-clock*) entre el envío de la pregunta
  y la recepción de la respuesta completa del agente.
* **Memoria**: incremento de memoria residente (RSS) del proceso del backend
  durante la ejecución, y pico aproximado (*peak*) por consulta.

Cada consulta se repite ``N_REPETICIONES`` veces y se reporta la mediana
(robusta frente a la primera ejecución "en frío", que carga el modelo en
Ollama). Los resultados se imprimen como una tabla y se vuelcan a un CSV
para incorporarlos al capítulo de Pruebas.

REQUISITOS para una medición real:
  - PostgreSQL en marcha (docker compose up db).
  - Ollama sirviendo el modelo qwen2.5 (ollama serve / ollama run qwen2.5).
  - pip install psutil

Uso:
  python -m tests.benchmark_rendimiento          # desde backend/
  python tests/benchmark_rendimiento.py
"""

import csv
import gc
import os
import statistics
import sys
import time
from datetime import datetime

# Permitir importar los módulos del backend.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

N_REPETICIONES = 5  # repeticiones por consulta (se descarta la 1.ª "en frío")

# Banco de consultas representativas, una por tipo de intención (Cap. 2).
CONSULTAS = [
    ("Visualización individual (HU-01)", "muéstrame el pib"),
    ("Comparación de métricas (HU-02)", "compara población rural y urbana"),
    ("Comparación entre países (HU-09)", "compara el pib entre España y Alemania"),
    ("Consulta numérica (HU-03)", "¿cuál es el promedio de obesidad?"),
    ("Descripción de indicador (HU-11)", "¿qué es la estabilidad política?"),
    ("Exploración de datos (HU-04)", "¿qué datos tienes?"),
    ("Navegación (HU-06)", "llévame al inicio"),
    # La predicción es deliberadamente pesada (ejecuta SARIMAX):
    ("Predicción estadística (HU-10)", "predice el trigo en grecia"),
]


def _memoria_rss_mb():
    """Memoria residente del proceso en MB (requiere psutil)."""
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        return float("nan")


def _medir_una(agent_service, pregunta):
    """Mide latencia (s) e incremento de RSS (MB) de una sola llamada."""
    gc.collect()
    rss_antes = _memoria_rss_mb()
    t0 = time.perf_counter()
    _ = agent_service.chat_with_agent(pregunta)
    latencia = time.perf_counter() - t0
    delta_rss = _memoria_rss_mb() - rss_antes
    return latencia, delta_rss


def main():
    print("Cargando el agente (esto inicializa el LLM y el catálogo)...")
    try:
        from agent import agent_service
    except Exception as exc:
        print(f"\n[ERROR] No se pudo cargar el agente: {exc}")
        print("Asegúrate de tener LangChain/Ollama y la BD disponibles.")
        sys.exit(1)

    print(f"Memoria base del proceso: {_memoria_rss_mb():.1f} MB\n")

    filas = []
    encabezado = f"{'Intención':<38}{'Latencia med. (s)':>18}{'Min-Max (s)':>16}{'ΔRSS med. (MB)':>16}"
    print(encabezado)
    print("-" * len(encabezado))

    for etiqueta, pregunta in CONSULTAS:
        latencias, deltas = [], []
        for i in range(N_REPETICIONES):
            lat, drss = _medir_una(agent_service, pregunta)
            # Descartamos la 1.ª iteración (carga en frío del modelo).
            if i > 0:
                latencias.append(lat)
                deltas.append(drss)
        if not latencias:  # N_REPETICIONES == 1
            latencias, deltas = [lat], [drss]

        lat_med = statistics.median(latencias)
        lat_min, lat_max = min(latencias), max(latencias)
        drss_med = statistics.median(deltas)

        print(f"{etiqueta:<38}{lat_med:>18.2f}{f'{lat_min:.2f}-{lat_max:.2f}':>16}{drss_med:>16.1f}")
        filas.append({
            "intencion": etiqueta,
            "consulta": pregunta,
            "latencia_mediana_s": round(lat_med, 3),
            "latencia_min_s": round(lat_min, 3),
            "latencia_max_s": round(lat_max, 3),
            "delta_rss_mediana_mb": round(drss_med, 2),
            "n_muestras": len(latencias),
        })

    # Volcado a CSV.
    salida = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"benchmark_resultados_{datetime.now():%Y%m%d_%H%M}.csv",
    )
    with open(salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        writer.writeheader()
        writer.writerows(filas)

    print(f"\nResultados guardados en: {salida}")
    print("Copia esta tabla en la sección de pruebas de rendimiento del TFG.")


if __name__ == "__main__":
    main()
