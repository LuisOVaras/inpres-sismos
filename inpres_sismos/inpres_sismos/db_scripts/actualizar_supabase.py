import os
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# Configuración
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") # Usar Service Role Key para inserts

base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, '..', '..', '..', 'data', 'sismos.csv')

def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY no configuradas.")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Leer CSV
    if not os.path.exists(csv_path):
        print(f"Error: No se encuentra {csv_path}")
        return

    df = pd.read_csv(csv_path)
    
    # Tomar los últimos N registros o filtrar por fecha si es necesario
    # Para simplificar, intentaremos insertar los últimos 50 (que suelen ser los nuevos)
    # Supabase manejará los duplicados si tenemos una constraint unique o controlamos aquí.
    
    # Formatear datos para Supabase
    df_to_upload = df.copy()
    # Convertir fecha a formato ISO YYYY-MM-DD para Supabase si la columna es de tipo date
    df_to_upload['fecha_iso'] = pd.to_datetime(df_to_upload['fecha'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
    # Sentido a booleano
    df_to_upload['sentido_bool'] = df_to_upload['sentido'].apply(lambda x: True if x == 'Si' else False)
    
    records = []
    for _, row in df_to_upload.head(100).iterrows(): # Procesar los 100 más recientes
        records.append({
            "fecha": row['fecha_iso'],
            "hora": row['hora'],
            "latitud": float(row['latitud']),
            "longitud": float(row['longitud']),
            "profundidad": row['profundidad'],
            "magnitud": float(row['magnitud']),
            "provincia": row['provincia'],
            "sentido": row['sentido_bool']
        })

    print(f"Sincronizando {len(records)} registros con Supabase...")
    
    for record in records:
        try:
            # Intentar insertar. Si hay una constraint unique en (fecha, hora, latitud, longitud),
            # podemos usar upsert o simplemente capturar el error de duplicado.
            supabase.table("sismos").upsert(record, on_conflict="fecha,hora,latitud,longitud").execute()
        except Exception as e:
            print(f"Error al insertar registro {record['fecha']} {record['hora']}: {e}")

    print("Sincronización con Supabase finalizada.")

if __name__ == "__main__":
    main()
