"""
recent_exporter.py

Responsabilidad única: exportar los N registros más recientes como JSON plano.

Alternativa liviana al CSV completo para aplicaciones que solo necesitan
los sismos recientes (ej: mapas de tiempo real, notificaciones).

No modifica sismos.csv. No toca SQLite. No toca Supabase.
"""
import json
import os
import pandas as pd
from exporters.config import RECENT_OUT, EXPORTS_DIR, RECENT_LIMIT


def export(df: pd.DataFrame) -> None:
    """
    Genera data/exports/sismos_recientes.json con los últimos RECENT_LIMIT registros.

    El CSV ya está ordenado del más reciente al más antiguo (el scraper prepend).
    Se toman simplemente los primeros N registros.

    Args:
        df: DataFrame producido por csv_exporter.load_sismos()
    """
    df_recent = df.head(RECENT_LIMIT).copy()

    # Reemplazar NaN por None para que json.dump produzca null en lugar de NaN
    df_recent = df_recent.where(pd.notna(df_recent), other=None)

    records = df_recent.to_dict(orient="records")

    os.makedirs(EXPORTS_DIR, exist_ok=True)
    with open(RECENT_OUT, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, default=_serialize)

    print(f"  [OK] Recientes exportados: {len(records)} registros -> {RECENT_OUT}")


def _serialize(obj):
    """Convierte tipos no serializables por json.dump (ej: numpy floats)."""
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Tipo no serializable: {type(obj)}")
