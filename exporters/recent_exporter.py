"""
recent_exporter.py

Responsabilidad única: exportar los N registros más recientes como JSON plano,
incluyendo IDs determinísticos y la capa de datos de ubicación enriquecida.

Alternativa liviana al GeoJSON/CSV completo para aplicaciones que solo necesitan
los sismos recientes (ej: mapas de tiempo real, notificaciones).

No modifica sismos.csv, SQLite ni Supabase.
"""
import json
import os
import pandas as pd
from exporters.config import RECENT_OUT, EXPORTS_DIR, RECENT_LIMIT


def export(df: pd.DataFrame) -> None:
    """
    Genera data/exports/sismos_recientes.json con los últimos RECENT_LIMIT registros.

    Args:
        df: DataFrame producido por csv_exporter.load_sismos()
    """
    df_recent = df.head(RECENT_LIMIT).copy()

    # Formatear columnas para JSON plano limpio
    records = []
    for _, row in df_recent.iterrows():
        rec = {
            "id": str(row["id"]),
            "fecha": row.get("fecha", None),
            "hora": row.get("hora", None),
            "latitud": float(row["latitud"]) if pd.notna(row["latitud"]) else None,
            "longitud": float(row["longitud"]) if pd.notna(row["longitud"]) else None,
            "profundidad": float(row["profundidad"]) if pd.notna(row["profundidad"]) else None,
            "magnitud": float(row["magnitud"]) if pd.notna(row["magnitud"]) else None,
            "sentido": row.get("sentido", None),
            "ubicacion_original": row.get("ubicacion_original", None),
            "ubicacion_normalizada": row.get("ubicacion_normalizada", None),
            "provincia": row.get("provincia_normalizada", None),
            "provincias": row.get("provincias", []),
            "pais": row.get("pais", None),
            "tipo_ubicacion": row.get("tipo_ubicacion", None),
            "es_argentina": bool(row.get("es_argentina", False)),
            "es_limite": bool(row.get("es_limite", False)),
        }
        records.append(rec)

    os.makedirs(EXPORTS_DIR, exist_ok=True)
    with open(RECENT_OUT, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, default=_serialize)

    print(f"  [OK] Recientes exportados: {len(records)} registros -> {RECENT_OUT}")


def _serialize(obj):
    """Convierte tipos no serializables por json.dump (ej: numpy floats/bools)."""
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Tipo no serializable: {type(obj)}")
