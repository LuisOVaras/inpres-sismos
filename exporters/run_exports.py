"""
run_exports.py

Punto de entrada del sistema de exportación.
Lee sismos.csv una sola vez y ejecuta todos los exportadores en secuencia.

Uso:
    python exporters/run_exports.py

Este script es invocado por GitHub Actions al final del pipeline de scraping.
Si falla, el pipeline principal (scraping + SQLite + Supabase) no se ve afectado.
"""
import sys
import os

# Asegurar que el directorio raíz del repo esté en el path
# para que los imports de 'exporters.*' funcionen correctamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from exporters.config import SISMOS_CSV
from exporters import csv_exporter, geojson_exporter, metadata_exporter, recent_exporter


def main():
    print("=" * 60)
    print("GENERACIÓN DE ARCHIVOS DE EXPORTACIÓN")
    print("=" * 60)
    print(f"[CSV] Fuente: {SISMOS_CSV}")

    # Verificar que el CSV existe antes de intentar leerlo
    if not os.path.exists(SISMOS_CSV):
        print(f"[ERROR] No se encontro: {SISMOS_CSV}")
        sys.exit(1)

    # Leer el CSV una sola vez — todos los exportadores comparten el mismo DataFrame
    print("\n[1] Cargando sismos.csv...")
    df = csv_exporter.load_sismos()
    print(f"    {len(df)} registros cargados")


    errors = []

    # GeoJSON
    print("\n[2] Exportando GeoJSON...")
    try:
        geojson_exporter.export(df)
    except Exception as e:
        print(f"  [ERROR] GeoJSON fallo: {e}")
        errors.append("geojson")

    # Metadata
    print("\n[3] Exportando metadata...")
    try:
        metadata_exporter.export(df)
    except Exception as e:
        print(f"  [ERROR] Metadata fallo: {e}")
        errors.append("metadata")

    # Recientes
    print("\n[4] Exportando recientes...")
    try:
        recent_exporter.export(df)
    except Exception as e:
        print(f"  [ERROR] Recientes fallo: {e}")
        errors.append("recent")

    print("\n" + "=" * 60)
    if errors:
        print(f"[WARN] Completado con errores en: {', '.join(errors)}")
        print("       El pipeline principal no se ve afectado.")
        sys.exit(1)
    else:
        print("[OK] EXPORTACION COMPLETADA — todos los archivos generados")
    print("=" * 60)


if __name__ == "__main__":
    main()
