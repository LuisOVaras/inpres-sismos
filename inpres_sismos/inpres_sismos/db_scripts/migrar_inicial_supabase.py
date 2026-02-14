import os
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import time
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

# Configuración
# Puedes ponerlas aquí para la migración inicial manual o usar variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, '..', '..', '..', 'data', 'sismos.csv')

def migrate():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: Configura SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print(f"Leyendo datos desde {csv_path}...")
    df = pd.read_csv(csv_path)
    
    # Formatear datos
    df['fecha_iso'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
    df['sentido_bool'] = df['sentido'].apply(lambda x: True if x == 'Si' else False)
    
    records = []
    for _, row in df.iterrows():
        # Helper para limpiar floats y convertirlos a None si son NaN o inválidos
        def clean_float(val):
            try:
                if pd.isna(val): return None
                f = float(val)
                import math
                return f if not math.isnan(f) and not math.isinf(f) else None
            except:
                return None
        
        records.append({
            "fecha": row['fecha_iso'],
            "hora": row['hora'],
            "latitud": clean_float(row['latitud']),
            "longitud": clean_float(row['longitud']),
            "profundidad": str(row['profundidad']) if pd.notna(row['profundidad']) else None,
            "magnitud": clean_float(row['magnitud']),
            "provincia": row['provincia'] if pd.notna(row['provincia']) else None,
            "sentido": bool(row['sentido_bool']) if pd.notna(row['sentido_bool']) else False
        })

    total = len(records)
    batch_size = 500
    print(f"Iniciando migración de {total} registros en lotes de {batch_size}...")

    for i in range(0, total, batch_size):
        batch = records[i:i+batch_size]
        try:
            supabase.table("sismos").upsert(batch, on_conflict="fecha,hora,latitud,longitud").execute()
            print(f"  Procesados: {min(i + batch_size, total)}/{total}")
        except Exception as e:
            print(f"  Error en lote {i}-{i+batch_size}: {e}")
        
        time.sleep(0.5) # Evitar saturar la API

    print("\n¡Migración inicial completada!")

if __name__ == "__main__":
    migrate()
