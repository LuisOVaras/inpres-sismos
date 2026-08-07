"""
metadata_exporter.py

Responsabilidad única: generar un archivo JSON completo con metadatos del dataset.

Permite al frontend (React) conocer la versión, bounding box, estadísticas generales
y rangos de datos sin necesidad de descargar ni procesar todo el dataset.

No modifica sismos.csv, SQLite ni Supabase.
"""
import json
import os
from datetime import datetime, timezone
import pandas as pd
from exporters.config import METADATA_OUT, EXPORTS_DIR


def export(df: pd.DataFrame) -> None:
    """
    Genera data/exports/metadata.json a partir del DataFrame recibido.

    Args:
        df: DataFrame producido por csv_exporter.load_sismos()
    """
    total = len(df)

    # Parsear fechas para obtener rango (el CSV usa DD/MM/YYYY)
    fechas = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce").dropna()
    fecha_mas_reciente = fechas.max().strftime("%Y-%m-%d") if not fechas.empty else None
    fecha_mas_antigua = fechas.min().strftime("%Y-%m-%d") if not fechas.empty else None

    magnitudes = df["magnitud"].dropna()
    profundidades = df["profundidad"].dropna()
    lats = df["latitud"].dropna()
    lons = df["longitud"].dropna()

    # Bounding box completo del dataset
    west = float(lons.min()) if not lons.empty else None
    east = float(lons.max()) if not lons.empty else None
    south = float(lats.min()) if not lats.empty else None
    north = float(lats.max()) if not lats.empty else None

    # Listas y conteos de provincias normalizadas y países
    provincias_raw = sorted([p for p in df["ubicacion_original"].dropna().unique() if str(p).strip()])
    provincias_norm = sorted([p for p in df["provincia_normalizada"].dropna().unique() if str(p).strip()])
    paises = sorted([p for p in df["pais"].dropna().unique() if str(p).strip() and p != "Desconocido"])

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    metadata = {
        "schema_version": "2.0",
        "export_version": "2.0",
        "coordinate_reference_system": "EPSG:4326",
        "fecha_generacion_utc": now_utc,
        "ultima_actualizacion_utc": now_utc,
        "total_registros": total,
        "total_registros_exportados": total,
        "fecha_mas_reciente": fecha_mas_reciente,
        "fecha_mas_antigua": fecha_mas_antigua,
        "magnitud_maxima": round(float(magnitudes.max()), 1) if not magnitudes.empty else None,
        "magnitud_minima": round(float(magnitudes.min()), 1) if not magnitudes.empty else None,
        "magnitud_promedio": round(float(magnitudes.mean()), 2) if not magnitudes.empty else None,
        "profundidad_minima": round(float(profundidades.min()), 1) if not profundidades.empty else None,
        "profundidad_maxima": round(float(profundidades.max()), 1) if not profundidades.empty else None,
        "profundidad_promedio": round(float(profundidades.mean()), 1) if not profundidades.empty else None,
        "bounding_box": {
            "west": west,
            "east": east,
            "south": south,
            "north": north,
        },
        "cantidad_provincias_normalizadas": len(provincias_norm),
        "provincias_normalizadas": provincias_norm,
        "cantidad_paises": len(paises),
        "paises": paises,
        "provincias_raw": provincias_raw,
        "provincias": provincias_raw,  # Mantenido por retrocompatibilidad v1
        "fuente": "INPRES — Instituto Nacional de Prevención Sísmica de Argentina",
        "repositorio": "https://github.com/LuisOVaras/inpres-sismos",
    }

    os.makedirs(EXPORTS_DIR, exist_ok=True)
    with open(METADATA_OUT, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"  [OK] Metadata exportada: {total} registros -> {METADATA_OUT}")
