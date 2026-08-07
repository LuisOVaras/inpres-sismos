"""
csv_exporter.py

Responsabilidad única: leer sismos.csv, calcular el ID determinístico único por evento
y aplicar la capa de normalización de ubicación. Devuelve un DataFrame enriquecido
listo para ser consumido por los demás exportadores.

No escribe ningún archivo. No modifica sismos.csv, SQLite ni Supabase.
"""
import hashlib
import pandas as pd
from exporters.config import SISMOS_CSV
from exporters.location_normalizer import normalize_location


def make_deterministic_id(row: pd.Series) -> str:
    """
    Genera un hash SHA-256 determinístico y estable de 16 caracteres hexadecimales.
    Basado en los atributos fundamentales e inmutables del evento sísmico.
    """
    fecha = str(row.get("fecha", "")).strip()
    hora = str(row.get("hora", "")).strip()
    lat = f"{float(row['latitud']):.4f}" if pd.notna(row.get("latitud")) else ""
    lon = f"{float(row['longitud']):.4f}" if pd.notna(row.get("longitud")) else ""
    prof = f"{float(row['profundidad']):.1f}" if pd.notna(row.get("profundidad")) else ""
    mag = f"{float(row['magnitud']):.1f}" if pd.notna(row.get("magnitud")) else ""

    raw_key = f"{fecha}|{hora}|{lat}|{lon}|{prof}|{mag}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]


def load_sismos() -> pd.DataFrame:
    """
    Lee sismos.csv y devuelve un DataFrame con tipos normalizados, IDs determinísticos
    y campos de ubicación enriquecidos.

    Conversiones aplicadas:
    - profundidad: extrae valor numérico (quita ' Km' si está presente)
    - magnitud, latitud, longitud, profundidad: numérico
    - id: SHA-256 de 16 caracteres
    - campos de ubicación enriquecidos (provincia_normalizada, pais, es_argentina, etc.)

    No modifica el CSV de origen.
    """
    df = pd.read_csv(SISMOS_CSV)

    # Profundidad: puede venir como "10 Km" o "10"
    if df["profundidad"].dtype == object:
        df["profundidad"] = (
            df["profundidad"]
            .str.replace(" Km", "", regex=False)
            .str.strip()
        )

    df[["magnitud", "latitud", "longitud", "profundidad"]] = df[
        ["magnitud", "latitud", "longitud", "profundidad"]
    ].apply(pd.to_numeric, errors="coerce")

    # Generar ID determinístico de 16 caracteres
    df["id"] = df.apply(make_deterministic_id, axis=1)

    # Enriquecer ubicación usando location_normalizer
    loc_meta = df["provincia"].apply(normalize_location)

    df["ubicacion_original"] = df["provincia"]
    df["ubicacion_normalizada"] = loc_meta.apply(lambda d: d["ubicacion_normalizada"])
    df["provincia_normalizada"] = loc_meta.apply(lambda d: d["provincia"])
    df["provincias"] = loc_meta.apply(lambda d: d["provincias"])
    df["pais"] = loc_meta.apply(lambda d: d["pais"])
    df["tipo_ubicacion"] = loc_meta.apply(lambda d: d["tipo_ubicacion"])
    df["es_argentina"] = loc_meta.apply(lambda d: d["es_argentina"])
    df["es_limite"] = loc_meta.apply(lambda d: d["es_limite"])

    return df
