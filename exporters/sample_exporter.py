"""
sample_exporter.py

Responsabilidad única: generar sample.geojson con una muestra variada y representativa
de entre 100 y 300 eventos sísmicos.

Permite desarrollar y probar la interfaz (React + MapLibre) rápidamente sin necesidad
de cargar ni procesar los 20MB del GeoJSON completo.

No modifica sismos.csv, SQLite ni Supabase.
"""
import json
import os
import pandas as pd
from exporters.config import SAMPLE_OUT, EXPORTS_DIR, SAMPLE_TARGET_SIZE


def export(df: pd.DataFrame) -> None:
    """
    Genera data/exports/sample.geojson con entre 100 y 300 registros variados.

    Args:
        df: DataFrame producido por csv_exporter.load_sismos()
    """
    df_valid = df.dropna(subset=["latitud", "longitud"]).copy()

    if len(df_valid) == 0:
        print("  [WARN] No hay registros con coordenadas para sample.geojson")
        return

    # Selección estratificada para garantizar variabilidad
    samples = []

    # 1. Todos los sismos de magnitud >= 6.0
    mag_altas = df_valid[df_valid["magnitud"] >= 6.0]
    samples.append(mag_altas)

    # 2. Muestra de sismos sentidos
    sentidos = df_valid[df_valid["sentido"] == "Si"]
    if len(sentidos) > 0:
        samples.append(sentidos.sample(n=min(40, len(sentidos)), random_state=42))

    # 3. Muestra de eventos internacionales / limítrofes / oceánicos
    no_arg = df_valid[~df_valid["es_argentina"] | df_valid["es_limite"]]
    if len(no_arg) > 0:
        samples.append(no_arg.sample(n=min(30, len(no_arg)), random_state=42))

    # 4. Muestra representativa de sismos recientes
    recientes = df_valid.head(200)
    samples.append(recientes.sample(n=min(50, len(recientes)), random_state=42))

    # 5. Muestra distribuida aleatoriamente del resto del dataset
    resto_n = max(50, SAMPLE_TARGET_SIZE - sum(len(s) for s in samples))
    resto = df_valid.sample(n=min(resto_n, len(df_valid)), random_state=42)
    samples.append(resto)

    # Combinar y eliminar duplicados manteniendo el orden
    df_sample = pd.concat(samples).drop_duplicates(subset=["id"])

    # Ajustar tamaño final entre 100 y 300
    if len(df_sample) > 300:
        df_sample = df_sample.head(300)
    elif len(df_sample) < 100 and len(df_valid) >= 100:
        df_sample = df_valid.sample(n=150, random_state=42)

    features = []
    for _, row in df_sample.iterrows():
        feature_id = str(row["id"])
        
        feature = {
            "type": "Feature",
            "id": feature_id,
            "geometry": {
                "type": "Point",
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
    with open(SAMPLE_OUT, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, default=_serialize)

    print(f"  [OK] Sample GeoJSON exportado: {len(features)} features -> {SAMPLE_OUT}")


def _serialize(obj):
    """Convierte tipos no serializables por json.dump (ej: numpy floats/bools)."""
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Tipo no serializable: {type(obj)}")
