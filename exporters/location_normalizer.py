"""
location_normalizer.py

Módulo independiente para normalizar nombres de provincia y ubicación.
No modifica el CSV fuente, SQLite ni Supabase.

Transforma cadenas raw de ubicación (con errores de tipeo, variantes de límites,
encoding roto, etc.) en información estructurada y limpia para el frontend.
"""

import re
from typing import Dict, Any, Optional, List


def normalize_location(raw_location: Optional[str]) -> Dict[str, Any]:
    """
    Recibe la cadena raw de provincia/ubicación y devuelve un diccionario enriquecido.

    Campos devueltos:
    - ubicacion_original (str): Valor original intacto.
    - ubicacion_normalizada (str): Nombre legible y estandarizado.
    - provincia (str | None): Nombre de la provincia argentina principal (si aplica).
    - provincias (list[str]): Lista de provincias argentinas involucradas.
    - pais (str): Nombre del país (ej: "Argentina", "Chile", "Bolivia").
    - tipo_ubicacion (str): "provincia", "limite_interprovincial", "limite_internacional", "extranjero", "oceano", "antartida", "desconocido".
    - es_argentina (bool): True si pertenece a Argentina (incluye sector Antártico y mares nacionales).
    - es_limite (bool): True si corresponde a una zona fronteriza o límite.
    """
    if not raw_location or not isinstance(raw_location, str) or not raw_location.strip():
        return {
            "ubicacion_original": raw_location,
            "ubicacion_normalizada": "Desconocido",
            "provincia": None,
            "provincias": [],
            "pais": "Desconocido",
            "tipo_ubicacion": "desconocido",
            "es_argentina": False,
            "es_limite": False,
        }

    original = raw_location.strip()
    s = original.upper()

    # Sanitización inicial de caracteres rotos de encoding o tipeo
    s = s.replace("\ufffd", "").replace("}", "").replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()

    # Fixes específicos de encoding/tipeo directo
    if "CÁRDOBA" in s or "CORDOBA" in s or "C RDOBA" in s:
        s = s.replace("CÁRDOBA", "CORDOBA").replace("C RDOBA", "CORDOBA")
    if "TUCUMÁN" in s or "TUCUMN" in s:
        s = s.replace("TUCUMÁN", "TUCUMAN").replace("TUCUMN", "TUCUMAN")
    if "REPÚBLICA" in s or "REP BLICA" in s:
        s = s.replace("REPÚBLICA", "REPUBLICA").replace("REP BLICA", "REPUBLICA")
    if s.startswith("MENDOZA") or "MMENDOZA" in s or "MENDOZA" in s:
        s = s.replace("MMENDOZA", "MENDOZA")
    if "SGO DEL ESTERO" in s or "SGO.DEL ESTERO" in s or "SGO DEL" in s:
        s = s.replace("SGO DEL ESTERO", "SANTIAGO DEL ESTERO").replace("SGO.DEL ESTERO", "SANTIAGO DEL ESTERO")

    # Mapeo de provincias canónicas argentinas y sus nombres limpios
    CANONICAL_PROVINCES = {
        "SAN JUAN": "San Juan",
        "SALTA": "Salta",
        "JUJUY": "Jujuy",
        "LA RIOJA": "La Rioja",
        "MENDOZA": "Mendoza",
        "CATAMARCA": "Catamarca",
        "CORDOBA": "Córdoba",
        "SAN LUIS": "San Luis",
        "NEUQUEN": "Neuquén",
        "TUCUMAN": "Tucumán",
        "SANTIAGO DEL ESTERO": "Santiago del Estero",
        "SANTA CRUZ": "Santa Cruz",
        "RIO NEGRO": "Río Negro",
        "LA PAMPA": "La Pampa",
        "CHACO": "Chaco",
        "FORMOSA": "Formosa",
        "ENTRE RIOS": "Entre Ríos",
        "CORRIENTES": "Corrientes",
        "CHUBUT": "Chubut",
        "BUENOS AIRES": "Buenos Aires",
        "TIERRA DEL FUEGO": "Tierra del Fuego, Antártida e Islas del Atlántico Sur",
    }

    # 1. CASO TFAIAS / TIERRA DEL FUEGO (verificado por evidencia geográfica)
    if "TFAIAS" in original.upper() or "TIERRA DEL FUEGO" in s:
        prov_name = "Tierra del Fuego, Antártida e Islas del Atlántico Sur"
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": prov_name,
            "provincia": prov_name,
            "provincias": [prov_name],
            "pais": "Argentina",
            "tipo_ubicacion": "provincia",
            "es_argentina": True,
            "es_limite": False,
        }

    # 2. CASOS DE LÍMITE INTERNACIONAL
    if any(k in s for k in ["LIM ARG-CHILE", "ARGENTINA-CHILE", "CHILE-ARGENTINA", "ARGENTINA CHILE", "LIM ARG-CHI"]):
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Límite Argentina - Chile",
            "provincia": None,
            "provincias": [],
            "pais": "Argentina / Chile",
            "tipo_ubicacion": "limite_internacional",
            "es_argentina": True,
            "es_limite": True,
        }

    # 3. CASOS DE LÍMITES INTERPROVINCIALES
    is_limite = any(k in s for k in ["LIM", "LIMITE", "CON"]) and not any(k in s for k in ["CHILE", "BOLIVIA", "PERU"])
    
    # Extraer qué provincias se mencionan en la cadena (en orden de aparición)
    matched_provinces: List[str] = []

    provincias_search = [
        ("SAN JUAN", "San Juan"),
        ("SAN JUA", "San Juan"),
        ("SALTA", "Salta"),
        ("JUJUY", "Jujuy"),
        ("LA RIOJA", "La Rioja"),
        ("RIOJA", "La Rioja"),
        ("MENDOZA", "Mendoza"),
        ("CATAMARCA", "Catamarca"),
        ("CORDOBA", "Córdoba"),
        ("SAN LUIS", "San Luis"),
        ("TUCUMAN", "Tucumán"),
        ("SANTIAGO DEL ESTERO", "Santiago del Estero"),
    ]

    for kw, canon_name in provincias_search:
        if kw in s and canon_name not in matched_provinces:
            matched_provinces.append(canon_name)

    if is_limite and len(matched_provinces) > 0:
        main_prov = matched_provinces[0]
        norm_title = f"Límite {' - '.join(matched_provinces)}"
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": norm_title,
            "provincia": main_prov,
            "provincias": matched_provinces,
            "pais": "Argentina",
            "tipo_ubicacion": "limite_interprovincial",
            "es_argentina": True,
            "es_limite": True,
        }

    # 4. PROVINCIAS DIRECTAS DE ARGENTINA (sin límites)
    if len(matched_provinces) == 1 and not is_limite:
        main_prov = matched_provinces[0]
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": main_prov,
            "provincia": main_prov,
            "provincias": [main_prov],
            "pais": "Argentina",
            "tipo_ubicacion": "provincia",
            "es_argentina": True,
            "es_limite": False,
        }

    for key, name in CANONICAL_PROVINCES.items():
        if key in s and not is_limite:
            return {
                "ubicacion_original": original,
                "ubicacion_normalizada": name,
                "provincia": name,
                "provincias": [name],
                "pais": "Argentina",
                "tipo_ubicacion": "provincia",
                "es_argentina": True,
                "es_limite": False,
            }

    # 5. PAÍSES EXTRANJEROS
    if "CHILE" in s:
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Chile",
            "provincia": None,
            "provincias": [],
            "pais": "Chile",
            "tipo_ubicacion": "extranjero",
            "es_argentina": False,
            "es_limite": "LIM" in s or "MAULE" in s,
        }
    if "BOLIVIA" in s:
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Bolivia",
            "provincia": None,
            "provincias": [],
            "pais": "Bolivia",
            "tipo_ubicacion": "extranjero",
            "es_argentina": False,
            "es_limite": False,
        }
    if "PERU" in s or "PERÚ" in s:
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Perú",
            "provincia": None,
            "provincias": [],
            "pais": "Perú",
            "tipo_ubicacion": "extranjero",
            "es_argentina": False,
            "es_limite": False,
        }
    if "PARAGUAY" in s:
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Paraguay",
            "provincia": None,
            "provincias": [],
            "pais": "Paraguay",
            "tipo_ubicacion": "extranjero",
            "es_argentina": False,
            "es_limite": False,
        }
    if "FILIPINAS" in s:
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Filipinas",
            "provincia": None,
            "provincias": [],
            "pais": "Filipinas",
            "tipo_ubicacion": "extranjero",
            "es_argentina": False,
            "es_limite": False,
        }
    if "NEW ZEALAND" in s:
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Nueva Zelanda",
            "provincia": None,
            "provincias": [],
            "pais": "Nueva Zelanda",
            "tipo_ubicacion": "extranjero",
            "es_argentina": False,
            "es_limite": False,
        }
    if "KURIL" in s:
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Islas Kuriles",
            "provincia": None,
            "provincias": [],
            "pais": "Rusia / Japón",
            "tipo_ubicacion": "extranjero",
            "es_argentina": False,
            "es_limite": False,
        }

    # 6. OCEÁNOS, MARES E ISLAS
    if "ATLANTICO" in s or "MAR ARGENTINO" in s:
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Océano Atlántico Sur",
            "provincia": None,
            "provincias": [],
            "pais": "Océano Atlántico",
            "tipo_ubicacion": "oceano",
            "es_argentina": True,
            "es_limite": False,
        }
    if "PACIFICO" in s:
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Océano Pacífico",
            "provincia": None,
            "provincias": [],
            "pais": "Océano Pacífico",
            "tipo_ubicacion": "oceano",
            "es_argentina": False,
            "es_limite": False,
        }
    if "DRAKE" in s or "SCOTIA" in s:
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Pasaje de Drake / Mar de Scotia",
            "provincia": None,
            "provincias": [],
            "pais": "Océano Antártico",
            "tipo_ubicacion": "oceano",
            "es_argentina": True,
            "es_limite": False,
        }
    if "ANTART" in s or "NTARTIDA" in s:
        tfaias_name = "Tierra del Fuego, Antártida e Islas del Atlántico Sur"
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Antártida Argentina",
            "provincia": tfaias_name,
            "provincias": [tfaias_name],
            "pais": "Argentina",
            "tipo_ubicacion": "antartida",
            "es_argentina": True,
            "es_limite": False,
        }
    if "SANDWICH" in s or "GEORGIA" in s or "ORCADAS" in s or "SHETLAND" in s:
        tfaias_name = "Tierra del Fuego, Antártida e Islas del Atlántico Sur"
        return {
            "ubicacion_original": original,
            "ubicacion_normalizada": "Islas del Atlántico Sur",
            "provincia": tfaias_name,
            "provincias": [tfaias_name],
            "pais": "Argentina",
            "tipo_ubicacion": "provincia",
            "es_argentina": True,
            "es_limite": False,
        }

    # 7. CASOS SIN CLASIFICAR / DUDOSOS -> CONSERVAR ORIGINAL SIN INVENTAR
    return {
        "ubicacion_original": original,
        "ubicacion_normalizada": original,
        "provincia": None,
        "provincias": [],
        "pais": "Desconocido",
        "tipo_ubicacion": "desconocido",
        "es_argentina": False,
        "es_limite": False,
    }
