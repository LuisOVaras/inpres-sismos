"""
stats_exporter.py

Responsabilidad única: generar stats.json con agregaciones precalculadas útiles.

Evita que el frontend (React) tenga que realizar bucles y agrupaciones costosas
sobre los 80,000+ registros al cargar dashboards o componentes de estadísticas.

No modifica sismos.csv, SQLite ni Supabase.
"""
import json
import os
import pandas as pd
from exporters.config import STATS_OUT, EXPORTS_DIR


def export(df: pd.DataFrame) -> None:
    """
    Genera data/exports/stats.json a partir del DataFrame recibido.

    Args:
        df: DataFrame producido por csv_exporter.load_sismos()
    """
    df_valid = df.copy()

    # Parsear fechas (DD/MM/YYYY)
    fechas = pd.to_datetime(df_valid["fecha"], format="%d/%m/%Y", errors="coerce")
    df_valid["anio"] = fechas.dt.year
    df_valid["mes"] = fechas.dt.month

    # 1. Sismos por año
    por_anio = (
        df_valid["anio"]
        .dropna()
        .astype(int)
        .value_counts()
        .sort_index()
        .to_dict()
    )
    # Convertir claves a string para JSON
    por_anio_dict = {str(k): int(v) for k, v in por_anio.items()}

    # 2. Sismos por mes (1..12)
    por_mes_raw = (
        df_valid["mes"]
        .dropna()
        .astype(int)
        .value_counts()
        .sort_index()
        .to_dict()
    )
    meses_nombres = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    por_mes_dict = {meses_nombres.get(k, str(k)): int(v) for k, v in por_mes_raw.items()}

    # 3. Distribución por rangos de magnitud
    mags = df_valid["magnitud"].dropna()
    dist_magnitud = {
        "menor_2_0": int((mags < 2.0).sum()),
        "entre_2_0_y_2_9": int(((mags >= 2.0) & (mags < 3.0)).sum()),
        "entre_3_0_y_3_9": int(((mags >= 3.0) & (mags < 4.0)).sum()),
        "entre_4_0_y_4_9": int(((mags >= 4.0) & (mags < 5.0)).sum()),
        "entre_5_0_y_5_9": int(((mags >= 5.0) & (mags < 6.0)).sum()),
        "mayor_o_igual_6_0": int((mags >= 6.0).sum()),
    }

    # 4. Distribución por profundidad
    profs = df_valid["profundidad"].dropna()
    dist_profundidad = {
        "superficial_0_33km": int((profs <= 33.0).sum()),
        "intermedio_33_70km": int(((profs > 33.0) & (profs <= 70.0)).sum()),
        "profundo_mas_70km": int((profs > 70.0).sum()),
    }

    # 5. Distribución por provincia normalizada (top)
    por_provincia = (
        df_valid["provincia_normalizada"]
        .dropna()
        .value_counts()
        .to_dict()
    )

    # 6. Distribución por país
    por_pais = (
        df_valid["pais"]
        .dropna()
        .value_counts()
        .to_dict()
    )

    # 7. Sismos sentidos vs no sentidos
    sentidos = df_valid["sentido"].value_counts().to_dict()
    sentidos_dict = {
        "sentidos": int(sentidos.get("Si", 0)),
        "no_sentidos": int(sentidos.get("No", 0)),
    }

    # 8. Eventos destacados de magnitud extrema (top 15)
    top_mags = df_valid.sort_values(by="magnitud", ascending=False).head(15)
    destacados = []
    for _, row in top_mags.iterrows():
        destacados.append({
            "id": str(row["id"]),
            "fecha": row.get("fecha", None),
            "hora": row.get("hora", None),
            "magnitud": float(row["magnitud"]) if pd.notna(row["magnitud"]) else None,
            "profundidad": float(row["profundidad"]) if pd.notna(row["profundidad"]) else None,
            "latitud": float(row["latitud"]) if pd.notna(row["latitud"]) else None,
            "longitud": float(row["longitud"]) if pd.notna(row["longitud"]) else None,
            "ubicacion_normalizada": row.get("ubicacion_normalizada", None),
            "provincia": row.get("provincia_normalizada", None),
            "pais": row.get("pais", None),
            "sentido": row.get("sentido", None),
        })

    stats = {
        "total_registros_analizados": len(df_valid),
        "sismos_por_anio": por_anio_dict,
        "sismos_por_mes": por_mes_dict,
        "distribucion_magnitud": dist_magnitud,
        "distribucion_profundidad": dist_profundidad,
        "distribucion_provincia": por_provincia,
        "distribucion_pais": por_pais,
        "sismos_sentidos_vs_no": sentidos_dict,
        "eventos_destacados_magnitud": destacados,
    }

    os.makedirs(EXPORTS_DIR, exist_ok=True)
    with open(STATS_OUT, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"  [OK] Estadísticas exportadas -> {STATS_OUT}")
