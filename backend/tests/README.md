# Batería de pruebas del backend

Pruebas automáticas del prototipo (pytest). Cubren pruebas unitarias, de
integración, de validación (historias de usuario) y un banco de rendimiento.

## Instalación

```bash
pip install pytest pyyaml psutil
# Para integración/rendimiento completos:
pip install -r requirements.txt   # langchain, fastapi, sqlalchemy, psycopg2...
```

## Ejecución

```bash
cd backend

pytest                 # toda la batería (omitir lo que no tenga servicios)
pytest -m "not db and not llm"   # solo unitarias (sin PostgreSQL ni Ollama)
pytest -m db           # integración con la base de datos
pytest -m "integracion"          # extremo a extremo (requiere BD + Ollama)
pytest -v              # detalle por caso
```

## Marcadores (markers)

- `db`  : requiere PostgreSQL en marcha.
- `llm` : requiere el modelo local (Ollama + qwen2.5).
- `integracion` : prueba entre varios componentes.

Las pruebas que requieren servicios externos se **omiten**  de forma
automática si éstos no están disponibles, de modo que el subconjunto unitario
siempre puede ejecutarse en cualquier entorno (incluida integración continua).

## Rendimiento

```bash
python tests/benchmark_rendimiento.py
```

Genera un CSV con la latencia (mediana, min-max) y el incremento de memoria
por tipo de intención. Requiere BD + Ollama y `psutil`.
