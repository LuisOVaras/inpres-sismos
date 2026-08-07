"""
csv_exporter.py

Responsabilidad única: leer sismos.csv y devolver un DataFrame normalizado
listo para ser consumido por los demás exportadores.

No escribe ningún archivo. No modifica datos.
"""
import pandas as pd
from exporters.config import SISMOS_CSV


def load_sismos() -> pd.DataFrame:
    """
    Lee sismos.csv y devuelve un DataFrame con tipos normalizados.

    Conversiones aplicadas:
    - profundidad: extrae valor numérico (quita ' Km' si está presente)
    - magnitud, latitud, longitud: numérico
    - fecha: string DD/MM/YYYY (se conserva el formato original del pipeline)

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

    return df
