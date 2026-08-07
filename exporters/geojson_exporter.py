"""
geojson_exporter.py

Responsabilidad única: convertir los sismos a formato GeoJSON estándar (RFC 7946)
y escribir el resultado en data/exports/sismos.geojson.

Formato de salida: FeatureCollection con geometry.Point (lon, lat),
id determinístico de 16 caracteres en cada Feature y propiedades enriquecidas.

Consumible directamente por MapLibre GL JS y Leaflet.

No modifica sismos.csv, SQLite ni Supabase.
"""
import json
import os
import pandas as pd
from exporters.config import GEOJSON_OUT, EXPORTS_DIR


def export(df: pd.DataFrame) -> None:
    """
    Genera data/exports/sismos.geojson a partir del DataFrame recibido.

    Args:
        df: DataFrame producido por csv_exporter.load_sismos()
    """
    # Filtrar filas sin coordenadas (no se pueden representar en GeoJSON)
    df_geo = df.dropna(subset=["latitud", "longitud"]).copy()

    features = []
    for _, row in df_geo.iterrows():
        feature_id = str(row["id"])
        
        feature = {
            "type": "Feature",
            "id": feature_id,
            "geometry": {
                "type": "Point",
                # GeoJSON usa [longitud, latitud] según el estándar RFC 7946
                "coordinates": [row["longitud"], row["latitud"]],
            },
            "properties": {
                "id": feature_id,
                "fecha": row.get("fecha", None),
                "hora": row.get("hora", None),
                "latitud": row["latitud"] if pd.notna(row["latitud"]) else None,
                "longitud": row["longitud"] if pd.notna(row["longitud"]) else None,
                "profundidad": row["profundidad"] if pd.notna(row["profundidad"]) else None,
                "magnitud": row["magnitud"] if pd.notna(row["magnitud"]) else None,
                "sentido": row.get("sentido", None),
                "ubicacion_original": row.get("ubicacion_original", None),
                "ubicacion_normalizada": row.get("ubicacion_normalizada", None),
                "provincia": row.get("provincia_normalizada", None),
                "provincias": row.get("provincias", []),
                "pais": row.get("pais", None),
                "tipo_ubicacion": row.get("tipo_ubicacion", None),
                "es_argentina": bool(row.get("es_argentina", False)),
                "es_limite": bool(row.get("es_limite", False)),
            },
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    os.makedirs(EXPORTS_DIR, exist_ok=True)
    with open(GEOJSON_OUT, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, default=_serialize)

    print(f"  [OK] GeoJSON exportado: {len(features)} features -> {GEOJSON_OUT}")


def _serialize(obj):
    """Convierte tipos no serializables por json.dump (ej: numpy floats/bools)."""
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Tipo no serializable: {type(obj)}")
