"""Servicio de catálogo de métricas."""

import difflib
from typing import List, Optional

import yaml

from models import Metrica


class MetricasConfig:
    """Carga el catálogo de métricas desde ``config.yaml`` y centraliza su búsqueda.

    Reúne en un único punto la lógica de identificación de una métrica a partir
    del lenguaje del usuario (alias exacto -> palabras clave -> similitud
    aproximada), que antes estaba duplicada en cada herramienta del agente.
    """

    def __init__(self, config_path: str) -> None:
        self._metricas: List[Metrica] = self._cargar(config_path)

    @staticmethod
    def _cargar(config_path: str) -> List[Metrica]:
        with open(config_path, "r", encoding="utf-8") as f:
            datasets = yaml.safe_load(f).get("datasets", [])
        return [
            Metrica(
                nombre=ds["nombre"],
                alias=ds.get("alias", []),
                unidad=ds.get("unidad", ""),
                descripcion=ds.get("descripcion", ""),
                insights=ds.get("insights", ""),
                categoria=ds.get("categoria"),
            )
            for ds in datasets
        ]

    @property
    def metricas(self) -> List[Metrica]:
        return self._metricas

    def listar_nombres(self) -> List[str]:
        return [m.nombre for m in self._metricas]

    def buscar(
        self,
        texto: str,
        *,
        alias_en_texto: bool = False,
        min_long: int = 2,
        min_coincidencias: int = 1,
    ) -> Optional[Metrica]:
        """Identifica la métrica que mejor encaja con ``texto``.

        Aplica tres pasos en orden: coincidencia por alias, por palabras clave
        en el nombre y, como último recurso, similitud aproximada (*fuzzy*).

        - ``alias_en_texto``: si ``True``, busca el alias DENTRO de ``texto``
          (para frases completas, p. ej. una pregunta); si ``False``, compara el
          alias y ``texto`` de forma directa (para consultas cortas).
        - ``min_long``: solo se consideran palabras de longitud mayor que este valor.
        - ``min_coincidencias``: número mínimo de palabras que deben coincidir en
          el nombre para aceptar la coincidencia por palabras clave.
        """
        t = texto.lower().strip()

        # PASO 1: coincidencia por alias
        for m in self._metricas:
            for alias in m.alias:
                a = alias.lower()
                if alias_en_texto:
                    if a in t:
                        return m
                elif a == t or t in a:
                    return m

        # PASO 2: palabras clave en el nombre (se elige el de más coincidencias)
        palabras = [w for w in t.split() if len(w) > min_long]
        mejor: Optional[Metrica] = None
        max_c = 0
        for m in self._metricas:
            nombre = m.nombre.lower()
            c = sum(1 for w in palabras if w in nombre)
            if c > max_c:
                max_c, mejor = c, m
        if mejor is not None and max_c >= min_coincidencias:
            return mejor

        # PASO 3: similitud aproximada (fuzzy)
        opciones = []  # pares (texto_de_busqueda, metrica)
        for m in self._metricas:
            opciones.append((m.nombre.lower(), m))
            for alias in m.alias:
                opciones.append((alias.lower(), m))
        cercanos = difflib.get_close_matches(t, [o[0] for o in opciones], n=1, cutoff=0.4)
        if cercanos:
            for texto_busqueda, m in opciones:
                if texto_busqueda == cercanos[0]:
                    return m
        return None
