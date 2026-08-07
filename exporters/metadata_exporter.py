"""
metadata_exporter.py

Responsabilidad única: generar un archivo JSON con metadatos del dataset.

Útil para que el segundo repositorio pueda saber, sin descargar el CSV completo:
- cuándo fue la última actualización
- cuántos registros hay
- rango de fechas y magnitudes disponibles
- provincias con datos

No modifica sismos.csv. No toca SQLite. No toca Supabase.
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
    provincias = sorted(df["provincia"].dropna().unique().tolist())

    metadata = {
        "total_registros": total,
        "fecha_mas_reciente": fecha_mas_reciente,
        "fecha_mas_antigua": fecha_mas_antigua,
        "magnitud_maxima": round(float(magnitudes.max()), 1) if not magnitudes.empty else None,
        "magnitud_minima": round(float(magnitudes.min()), 1) if not magnitudes.empty else None,
        "provincias": provincias,
        "ultima_actualizacion_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fuente": "INPRES — Instituto Nacional de Prevención Sísmica de Argentina",
        "repositorio": "https://github.com/LuisOVaras/inpres-sismos",
    }

    os.makedirs(EXPORTS_DIR, exist_ok=True)
    with open(METADATA_OUT, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"  [OK] Metadata exportada: {total} registros -> {METADATA_OUT}")
