import os
import re
import urllib.parse
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from database import db
import difflib
from metricas_config import MetricasConfig

_SARIMAX_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Sarimax', 'scripts'))

# 1. Configuración del Modelo

# 2. Cargar Configuración de Métricas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")

catalogo = MetricasConfig(CONFIG_PATH)

# 3. Definición de Herramientas (Tools)

def __obtener_query_paises(paises_str: str) -> str:
    if not paises_str:
        return f"&var-pais={urllib.parse.quote('España')}"
    import re
    parts = re.split(r',|\by\b|\be\b', paises_str, flags=re.IGNORECASE)
    parts = [p.strip() for p in parts if len(p.strip()) > 2]
    if not parts:
        return f"&var-pais={urllib.parse.quote('España')}"
    return "".join([f"&var-pais={urllib.parse.quote(p.title())}" for p in parts])


PAISES_CONOCIDOS = ["España", "Alemania", "Italia"]  # países cargados en la BD

def __extraer_paises_de_texto(texto: str) -> str:
    """Detecta países conocidos en 'texto' y los devuelve como cadena
    separada por comas, lista para el parámetro 'paises'."""
    t = texto.lower()
    encontrados = [p for p in PAISES_CONOCIDOS if p.lower() in t]
    return ", ".join(encontrados)


@tool
def buscar_y_graficar(query: str, paises: str = "") -> str:
    """
    Busca una métrica y genera automáticamente la URL de Grafana para visualizarla.
    Úsala cuando el usuario pida "ver", "mostrar", "graficar" o "visualizar" algo.
    Ejemplo: "quiero ver el pib", "muéstrame la obesidad", "población urbana"
    Puede indicarse uno o varios "paises" si el usuario lo pide.
    """
    print(f"🔎 DEBUG: Buscando y graficando: '{query}' en '{paises}'")
    if not paises:
        paises = __extraer_paises_de_texto(query)
    m = catalogo.buscar(query)
    if m is None:
        return "No encontré esa métrica. Intenta con: 'pib', 'obesidad', 'población', 'cereales', etc."
    base_url = "http://localhost:3000"
    dashboard_uid = "adj4dk7"
    nombre_safe = urllib.parse.quote(m.nombre)
    url = f"{base_url}/d/{dashboard_uid}/visor-actualizable?var-metrica={nombre_safe}{__obtener_query_paises(paises)}&kiosk"
    print(f"URL Generada: {url}")
    return url



@tool
def comparar_metricas(metricas: str, paises: str = "") -> str:
    """
    Compara MÚLTIPLES métricas en un solo gráfico de Grafana.
    Úsala cuando el usuario pida "comparar", "contrastar", "ver juntos", etc.
    
    Parámetro 'metricas': Lista de métricas separadas por comas o 'y'.
    Parámetro 'paises': (Opcional) Países a visualizar.
    Ejemplo: "población rural y urbana", "pib, obesidad, cereales"
    """
    print(f"DEBUG: Comparando métricas: '{metricas}' en '{paises}'")
    if not paises:                                 
        paises = __extraer_paises_de_texto(metricas)
    separadores = [',', ' y ', ' e ']
    queries = [metricas]
    for sep in separadores:
        new_queries = []
        for q in queries:
            new_queries.extend([s.strip() for s in q.split(sep)])
        queries = new_queries

    nombres_metricas = []
    for q in queries:
        if len(q.strip()) < 3:
            continue
        m = catalogo.buscar(q)
        if m is not None and m.nombre not in nombres_metricas:
            nombres_metricas.append(m.nombre)

    if len(nombres_metricas) == 0:
        return "No encontré ninguna métrica para comparar."

    base_url = "http://localhost:3000"
    dashboard_uid = "adj4dk7"
    if len(nombres_metricas) == 1:
        nombre_safe = urllib.parse.quote(nombres_metricas[0])
        return f"{base_url}/d/{dashboard_uid}/visor-actualizable?var-metrica={nombre_safe}{__obtener_query_paises(paises)}&kiosk"

    params = "&".join([f"var-metrica={urllib.parse.quote(n)}" for n in nombres_metricas])
    url = f"{base_url}/d/{dashboard_uid}/visor-actualizable?{params}{__obtener_query_paises(paises)}&kiosk"
    print(f"URL de comparación generada con {len(nombres_metricas)} métricas")
    return url




@tool
def comparar_paises(metrica: str, paises: str) -> str:
    """
    Compara UNA métrica entre MÚLTIPLES países en el visor actualizable.
    Úsala cuando el usuario quiera ver la misma métrica en varios países:
    "compara el PIB entre España y Francia", "obesidad en Italia y Alemania",
    "ver cereales en distintos países", "contrastar X entre países".

    Parámetro 'metrica': Nombre o alias de la métrica a comparar.
    Parámetro 'paises': Países separados por comas o 'y'.
    """
    print(f"DEBUG: Comparando países: métrica='{metrica}' paises='{paises}'")
    m = catalogo.buscar(metrica)
    if m is None:
        return "No encontré esa métrica. Intenta con: 'pib', 'obesidad', 'población', 'cereales', etc."
    nombre_metrica = m.nombre

    parts = re.split(r',|\by\b|\be\b', paises, flags=re.IGNORECASE)
    parts = [p.strip() for p in parts if len(p.strip()) > 2]
    if not parts:
        return "Por favor indica al menos un país. Ejemplo: 'España y Francia'."

    base_url = "http://localhost:3000"
    dashboard_uid = "adj4dk7"
    nombre_safe = urllib.parse.quote(nombre_metrica)
    query_paises = "".join([f"&var-pais={urllib.parse.quote(p.title())}" for p in parts])
    url = f"{base_url}/d/{dashboard_uid}/visor-actualizable?var-metrica={nombre_safe}{query_paises}&kiosk"
    print(f"URL comparación de países generada: {url}")
    return url





@tool
def consultar_datos_sql(pregunta: str) -> str:
    """
    Responde preguntas numéricas sobre los datos.
    Úsala para: "promedio", "máximo", "mínimo", "cuántos", "tendencia", "aumentado", "disminuido",
    o para consultar el valor de una métrica en un año concreto.
    
    Ejemplos: 
    - "¿Cuál es el promedio de obesidad?"
    - "¿Ha aumentado la población rural?"
    - "Dame el máximo del PIB"
    - "¿Cuál fue la producción de cereales en 2014?"
    - "PIB en el año 2020"
    """
    print(f"DEBUG: Consulta SQL para: '{pregunta}'")
    pregunta_lower = pregunta.lower()
    
    # Identificar la métrica mediante el catálogo (alias en la frase -> palabras clave -> fuzzy)
    m = catalogo.buscar(pregunta, alias_en_texto=True, min_long=3, min_coincidencias=2)
    if m is None:
        return "No pude identificar la métrica. Por favor especifica: PIB, obesidad, población, etc."

    nombre_metrica = m.nombre
    metrica_encontrada = {"nombre": m.nombre, "unidad": m.unidad, "insights": m.insights}
    print(f"   📊 Métrica identificada: {nombre_metrica}")

    # Detectar país mencionado (solo los países disponibles en la BD)
    PAISES_DISPONIBLES = {
        'españa': 'España', 'espana': 'España',
        'alemania': 'Alemania',
        'italia': 'Italia',
    }
    pais_encontrado = None
    for keyword, pais_normalizado in PAISES_DISPONIBLES.items():
        if keyword in pregunta_lower:
            pais_encontrado = pais_normalizado
            break

    pais_filter = f"AND d.pais = '{pais_encontrado}'" if pais_encontrado else ""
    pais_label = f" en {pais_encontrado}" if pais_encontrado else ""
    print(f"   🌍 País: {pais_encontrado or 'sin filtro'}")

    # Año mencionado en la pregunta (para acotar; p. ej. "desde 2020")
    match_año = re.search(r'\b(19\d{2}|20\d{2})\b', pregunta_lower)
    año_filtro = match_año.group(1) if match_año else None

    # Detectar tipo de consulta
    if any(word in pregunta_lower for word in ['promedio', 'media', 'average']):
        query = f"""
        SELECT ROUND(AVG(valor)::numeric, 2) as promedio
        FROM datos d
        JOIN metricas m ON d.metrica_id = m.id
        WHERE m.nombre = '{nombre_metrica}' {pais_filter}
        """
        tipo = "promedio"

    elif any(word in pregunta_lower for word in ['máximo', 'maximo', 'max', 'mayor']):
        query = f"""
        SELECT MAX(valor) as maximo,
               TO_CHAR(fecha, 'YYYY') as año
        FROM datos d
        JOIN metricas m ON d.metrica_id = m.id
        WHERE m.nombre = '{nombre_metrica}' {pais_filter}
        GROUP BY fecha
        ORDER BY maximo DESC
        LIMIT 1
        """
        tipo = "máximo"

    elif any(word in pregunta_lower for word in ['mínimo', 'minimo', 'min', 'menor']):
        query = f"""
        SELECT MIN(valor) as minimo,
               TO_CHAR(fecha, 'YYYY') as año
        FROM datos d
        JOIN metricas m ON d.metrica_id = m.id
        WHERE m.nombre = '{nombre_metrica}' {pais_filter}
        GROUP BY fecha
        ORDER BY minimo ASC
        LIMIT 1
        """
        tipo = "mínimo"

    elif any(word in pregunta_lower for word in ['cuántos', 'cuantos', 'count', 'cantidad']):
        query = f"""
        SELECT COUNT(*) as total_registros
        FROM datos d
        JOIN metricas m ON d.metrica_id = m.id
        WHERE m.nombre = '{nombre_metrica}' {pais_filter}
        """
        tipo = "conteo"

    elif any(word in pregunta_lower for word in ['tendencia', 'evolución', 'evolucion', 'aument', 'disminu', 'reduc', 'crec', 'subiendo', 'sube', 'bajando', 'bajado', 'desde']):
        # Por defecto, el primer valor de la serie; si se indica un año, desde ese año.
        filtro_inicio = f"AND fecha >= '{año_filtro}-01-01'" if año_filtro else ""
        query = f"""
        WITH primer_valor AS (
            SELECT TO_CHAR(fecha, 'YYYY') as año, valor
            FROM datos d
            JOIN metricas m ON d.metrica_id = m.id
            WHERE m.nombre = '{nombre_metrica}' {pais_filter} {filtro_inicio}
            ORDER BY fecha ASC
            LIMIT 1
        ),
        ultimo_valor AS (
            SELECT TO_CHAR(fecha, 'YYYY') as año, valor
            FROM datos d
            JOIN metricas m ON d.metrica_id = m.id
            WHERE m.nombre = '{nombre_metrica}' {pais_filter}
            ORDER BY fecha DESC
            LIMIT 1
        )
        SELECT
            p.año as año_inicio,
            ROUND(p.valor::numeric, 2) as valor_inicio,
            u.año as año_fin,
            ROUND(u.valor::numeric, 2) as valor_fin,
            ROUND((u.valor - p.valor)::numeric, 2) as cambio
        FROM primer_valor p, ultimo_valor u
        """
        tipo = "tendencia"

    else:
        if año_filtro:
            año_consultado = año_filtro
            query = f"""
            SELECT TO_CHAR(fecha, 'YYYY') as año, valor
            FROM datos d
            JOIN metricas m ON d.metrica_id = m.id
            WHERE m.nombre = '{nombre_metrica}' {pais_filter}
              AND TO_CHAR(fecha, 'YYYY') = '{año_consultado}'
            """
            tipo = "valor_en_año"
        else:
            query = f"""
            SELECT TO_CHAR(fecha, 'YYYY') as año, valor
            FROM datos d
            JOIN metricas m ON d.metrica_id = m.id
            WHERE m.nombre = '{nombre_metrica}' {pais_filter}
            ORDER BY fecha DESC
            LIMIT 5
            """
            tipo = "últimos valores"
    
    print(f"Tipo de consulta: {tipo}")
    
    try:
        resultados = db.run_query(query)
        
        if not resultados:
            msg = f"No hay datos disponibles para {nombre_metrica}{pais_label}."
            print(f"TOOL RETURN: {msg}")
            return msg

        # Formatear respuesta según el tipo
        if tipo == "promedio":
            valor = resultados[0]['promedio']
            insight = metrica_encontrada.get('insights', '')
            msg = f"El promedio de {nombre_metrica}{pais_label} es: {valor} {metrica_encontrada['unidad']}.\n\nContexto: {insight}"
            print(f"TOOL RETURN: {msg}")
            return msg

        elif tipo in ["máximo", "mínimo"]:
            valor = resultados[0].get('maximo') or resultados[0].get('minimo')
            año = resultados[0]['año']
            msg = f"El {tipo} de {nombre_metrica}{pais_label} fue {valor} {metrica_encontrada['unidad']} en el año {año}."
            print(f"TOOL RETURN: {msg}")
            return msg

        elif tipo == "conteo":
            total = resultados[0]['total_registros']
            msg = f"Hay {total} registros de datos para {nombre_metrica}{pais_label}."
            print(f"TOOL RETURN: {msg}")
            return msg

        elif tipo == "tendencia":
            r = resultados[0]
            cambio = r['cambio']
            if cambio > 0:
                direccion = "aumentado"
            elif cambio < 0:
                direccion = "disminuido"
            else:
                direccion = "se ha mantenido"
            insight = metrica_encontrada.get('insights', '')
            if direccion == "se ha mantenido":
                msg = f"{nombre_metrica}{pais_label} se ha mantenido en {r['valor_fin']} entre {r['año_inicio']} y {r['año_fin']}.\n\nContexto: {insight}"
            else:
                msg = f"{nombre_metrica}{pais_label} ha {direccion} de {r['valor_inicio']} ({r['año_inicio']}) a {r['valor_fin']} ({r['año_fin']}). Cambio total: {abs(cambio)} {metrica_encontrada['unidad']}.\n\nContexto: {insight}"
            print(f"TOOL RETURN: {msg}")
            return msg

        elif tipo == "valor_en_año":
            r = resultados[0]
            msg = f"En {r['año']}, {nombre_metrica}{pais_label} fue {r['valor']} {metrica_encontrada['unidad']}."
            print(f"TOOL RETURN: {msg}")
            return msg

        else:
            valores_str = "\n".join([f"  - {r['año']}: {r['valor']} {metrica_encontrada['unidad']}" for r in resultados])
            msg = f"Últimos valores de {nombre_metrica}{pais_label}:\n{valores_str}"
            print(f"TOOL RETURN: {msg}")
            return msg
    
    except Exception as e:
        print(f"Error SQL: {e}")
        return f"Error al consultar los datos: {str(e)}"
    


    

@tool
def describir_metrica(query: str) -> str:
    """
    Describe una métrica: qué mide, su unidad y análisis interpretativo.
    Úsala cuando el usuario pregunte "¿qué es?", "descríbeme", "explícame", "¿qué significa?", "interpretar", "analizar" una métrica.
    Ejemplo: "¿qué es el PIB?", "descríbeme la obesidad", "explica la estabilidad política"
    """
    print(f"DEBUG: Describiendo métrica: '{query}'")
    m = catalogo.buscar(query)
    if m is None:
        return "No encontré esa métrica. Intenta con: 'pib', 'obesidad', 'población', 'cereales', etc."
    return (
        f"**{m.nombre}**\n\n"
        f"Descripción: {m.descripcion or 'Sin descripción disponible.'}\n\n"
        f"Unidad de medida: {m.unidad or 'No especificada'}\n\n"
        f"Análisis e interpretación: {m.insights or 'No hay análisis disponible.'}"
    )


@tool
def listar_metricas_disponibles() -> str:
    """
    Lista TODAS las métricas disponibles en el sistema.
    Úsala cuando el usuario pregunte "¿qué datos tienes?" o "¿qué puedo ver?"
    """
    lista = [f"- {n}" for n in catalogo.listar_nombres()]
    return "Métricas disponibles (" + str(len(lista)) + " total):\n" + "\n".join(lista)



@tool
def ir_al_dashboard_principal(paises: str = "") -> str:
    """
    Navega a la pantalla del dashboard principal (el visor general, visor de datos fijos o inicial).
    Úselo cuando el usuario pida "ir al dashboard", "ver el dashboard", "muéstrame el dashboard fijo", "llévame al inicio".
    Parámetro 'paises': (Opcional) Países que se enviarán al dashboard principal.
    """
    
    if not paises:
        return "Volviendo al inicio...\nROUTE: /"
    
    query_paises = __obtener_query_paises(paises)
    # The helper string looks like "&var-pais=X&var-pais=Y"
    # We want to translate it to valid query url formatting like "/?pais=X&pais=Y"
    import urllib.parse
    # Just parse and rebuild for next router
    # We can just change '&var-pais=' to '?pais=' for the first one.
    query_paises = query_paises.replace('&var-', '&') # &pais=X&pais=Y
    if query_paises.startswith('&'):
        query_paises = '?' + query_paises[1:]
    
    return f"Enviando al Dashboard principal ({paises})...\nROUTE: /{query_paises}"

@tool
def predecir_trigo_grecia(dummy: str = "") -> str:
    """
    Realiza la predicción de la producción del trigo en Grecia usando un modelo SARIMAX.
    Úsala cuando el usuario pida "predice el trigo en grecia", "predicción de trigo", etc.
    Carga los últimos datos, ejecuta el modelo, guarda en BD y devuelve la explicación.
    """
    import sys as _sys
    if _SARIMAX_SCRIPTS_DIR not in _sys.path:
        _sys.path.insert(0, _SARIMAX_SCRIPTS_DIR)
    import script as _sarimax_script  # type: ignore[import]
    return _sarimax_script.predecir_trigo_grecia.func(dummy)

# 4. Creación del Agente

system_prompt = """Eres un asistente de datos. Tu ÚNICA función es usar las herramientas disponibles y devolver EXACTAMENTE lo que ellas te respondan.

HERRAMIENTAS DISPONIBLES:
1. `buscar_y_graficar`: Para VISUALIZAR una métrica (ej: "muéstrame el pib").
2. `comparar_metricas`: Para VISUALIZAR varias métricas juntas (ej: "compara población rural y urbana").
3. `comparar_paises`: Para comparar UNA métrica entre VARIOS países (ej: "compara el PIB entre España y Francia", "ver obesidad en Italia y Alemania").
4. `consultar_datos_sql`: Para RESPONDER preguntas numéricas (ej: "¿cuál es el promedio de obesidad?").
5. `describir_metrica`: Para EXPLICAR qué es una métrica, describirla e interpretarla (ej: "¿qué es el PIB?", "explícame la obesidad").
6. `listar_metricas_disponibles`: Si preguntan qué datos tienes.
7. `predecir_trigo_grecia`: Úsala SÓLO cuando el usuario pida "predice el trigo en grecia", "predicción de trigo", o similares.
8. `ir_al_dashboard_principal`: Para ir al dashboard general, inicial o regresar al inicio.

PROTOCOLO OBLIGATORIO:
1. Para TODA pregunta del usuario, DEBES usar una herramienta
2. Cuando una herramienta te devuelva un resultado, tu respuesta DEBE SER EXACTAMENTE ese resultado
3. NO añadas meta-comentarios, ni reflexiones, ni diálogos internos.
4. NUNCA digas cosas como "No necesitas usar la herramienta", "Aquí está la información", o "En este caso, la respuesta sería:". DA LA RESPUESTA DIRECTAMENTE Y NADA MÁS.
5. NO reformules ni resumas el output de la herramienta si son datos exactos.
6. Si la herramienta devuelve "El máximo de X fue Y en el año Z", tu respuesta es EXACTAMENTE eso.
7. NO censures términos médicos o de salud pública como 'obesidad', 'anemia', etc.
8. Si piden "ver", "mostrar", "gráfico" → USA `buscar_y_graficar` o `comparar_metricas`
9. Si piden comparar PAÍSES con UNA métrica (ej: "PIB de España y Francia") → USA `comparar_paises`
9. Si piden "promedio", "máximo", "tendencia", "ha aumentado", o el valor en un año concreto ("en 2014", "en el año 2020") → USA `consultar_datos_sql`
10. Si piden "qué es", "describir", "explicar", "interpretar", "analizar" → USA `describir_metrica`. Si la herramienta falla, DA LA DEFINICIÓN DIRECTAMENTE.
11. NUNCA EXPLIQUES TUS DECISIONES. NUNCA digas "La herramienta falló" o "Pero puedo darte una definición". ESCRIBE SOLO LA DEFINICIÓN (Ejemplo: "El PIB es...").
12. Si usas `listar_metricas_disponibles`, la herramienta devolverá una lista larga. IMPRIMELA TAL CUAL.
13. Si usas `predecir_trigo_grecia`, te devolverá una explicación larga y una directiva `ROUTE: /trigo`. Imprime el bloque de texto TAL CUAL, sin omitir la explicación matemática.

EJEMPLOS:

Usuario: "¿Cuál es el máximo del PIB?"
Herramienta `consultar_datos_sql` devuelve: "El máximo de PIB per cápita fue 45000 en el año 2019."
TU RESPUESTA EXACTA: "El máximo de PIB per cápita fue 45000 en el año 2019."

Usuario: "Muéstrame la obesidad"
TU ACCIÓN: Ejecuta `buscar_y_graficar(query="obesidad")`. ¡NO adivines la URL!

Usuario: "Predice el trigo en grecia"
TU ACCIÓN: Ejecuta `predecir_trigo_grecia()`. 

NO INVENTES URLES. USA LAS HERRAMIENTAS DIRECTAMENTE.
"""

class AgentService:
    """Servicio de orquestación del agente conversacional.

    Ensambla el LLM (ChatOllama), el conjunto de herramientas y el grafo de
    razonamiento ReAct (LangGraph), y expone chat_with_agent como punto de
    entrada único para todas las conversaciones.
    """

    PASSTHROUGH_TOOLS = {
        "predecir_trigo_grecia", "listar_metricas_disponibles", "buscar_y_graficar",
        "comparar_metricas", "comparar_paises", "ir_al_dashboard_principal",
        "consultar_datos_sql", "describir_metrica",
    }

    MENSAJE_POR_DEFECTO = (
        "No he podido procesar esa pregunta. Puedo mostrarte el gráfico de una "
        "métrica, compararla entre varias métricas o países, darte un valor "
        "concreto (promedio, máximo, mínimo, tendencia o el dato de un año), "
        "describir un indicador o listar los datos disponibles.\n\n"
        "Por ejemplo: «muéstrame el PIB de Italia», «promedio de obesidad en "
        "España», «compara la obesidad entre España y Alemania» o «¿qué datos tienes?»."
    )

    def __init__(self, model: str = "qwen2.5", temperature: float = 0) -> None:
        self._llm = ChatOllama(model=model, temperature=temperature)
        self._tools = [
            buscar_y_graficar, comparar_metricas, comparar_paises, consultar_datos_sql,
            describir_metrica, listar_metricas_disponibles, predecir_trigo_grecia,
            ir_al_dashboard_principal,
        ]
        self._tools_por_nombre = {t.name: t for t in self._tools}
        self._agent_executor = create_react_agent(
            self._llm, self._tools, prompt=SystemMessage(content=system_prompt)
        )

    def chat_with_agent(self, user_input: str) -> str:
        """Punto de entrada único para conversar con el agente."""
        try:
            response = self._agent_executor.invoke(
                {"messages": [("user", user_input)]},
                config={"recursion_limit": 50},
            )
            messages = response["messages"]

            # Para herramientas críticas, devolvemos su salida tal cual.
            for msg in reversed(messages):
                if type(msg).__name__ == "ToolMessage" and getattr(msg, "name", None) in self.PASSTHROUGH_TOOLS:
                    return msg.content

            # Red de seguridad: a veces el LLM "escribe" la llamada a la
            # herramienta como texto en lugar de ejecutarla. Si es el caso, la
            # ejecutamos nosotros.
            # Si ninguna herramienta se ejecutó, intentamos recuperar una llamada
            # escrita como texto; si tampoco, devolvemos un mensaje por defecto
            # en lugar del texto crudo (posiblemente alucinado) del modelo.
            final = messages[-1].content
            recuperado = self._ejecutar_si_es_tool_textual(final)
            if recuperado is not None:
                return recuperado
            return self.MENSAJE_POR_DEFECTO
        except Exception as e:
            return f"Error procesando la solicitud: {str(e)}"

    def _ejecutar_si_es_tool_textual(self, contenido: str):
        """Detecta una llamada a herramienta emitida como TEXTO por el LLM
        (p. ej. 'consultar_datos_sql({"pregunta": "..."})'), y si reconoce la
        herramienta, la ejecuta y devuelve su resultado. Devuelve None si el
        contenido no es una llamada reconocible.
        """
        import json
        m = re.match(r'^\s*([A-Za-z_]\w*)\s*\((\{.*\})?\)\s*$', contenido.strip(), re.DOTALL)
        if not m:
            return None
        nombre, args_json = m.group(1), m.group(2)
        tool = self._tools_por_nombre.get(nombre)
        if tool is None:
            return None
        try:
            args = json.loads(args_json) if args_json else {}
            return tool.invoke(args)
        except Exception:
            return None


# Instancia única del servicio, usada por la API (main.py).
agent_service = AgentService()