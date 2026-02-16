"""
Actualizar Supabase - Sincronización diaria de sismos desde CSV
Sincroniza los últimos registros del CSV con la base de datos Supabase
Compatible con estructura: inpres_sismos/inpres_sismos/db_scripts/
"""
import os
import sys
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import supabase
print("Supabase version:", supabase.__version__)
print("SUPABASE_URL:", SUPABASE_URL)

# Configuración
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Obtener ruta del CSV (3 niveles arriba desde db_scripts)
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, '..', '..', '..', 'data', 'sismos.csv')
csv_path = os.path.normpath(csv_path)

def clean_float(val):
    """Limpia valores float y convierte NaN/Inf a None"""
    try:
        if pd.isna(val):
            return None
        f = float(val)
        import math
        return f if not math.isnan(f) and not math.isinf(f) else None
    except:
        return None

def main():
    print("=" * 60)
    print("SINCRONIZACIÓN CON SUPABASE")
    print("=" * 60)
    
    # Validar credenciales
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY no configuradas.")
        print("   Verifica que los secrets estén configurados en GitHub.")
        sys.exit(1)

    # Validar archivo CSV
    if not os.path.exists(csv_path):
        print(f"❌ Error: No se encuentra el archivo CSV en {csv_path}")
        sys.exit(1)

    print(f"📂 Archivo CSV: {csv_path}")

    try:
        # Crear cliente Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conexión a Supabase establecida")

        # Leer CSV
        df = pd.read_csv(csv_path)
        print(f"📊 Registros en CSV: {len(df)}")
        
        # Formatear datos para Supabase
        df_to_upload = df.copy()
        
        # Convertir fecha a formato ISO YYYY-MM-DD
        df_to_upload['fecha_iso'] = pd.to_datetime(
            df_to_upload['fecha'], 
            format='%d/%m/%Y',
            errors='coerce'
        ).dt.strftime('%Y-%m-%d')
        
        # Sentido a booleano
        df_to_upload['sentido_bool'] = df_to_upload['sentido'].apply(
            lambda x: True if str(x).strip().lower() in ['si', 'sí', 'yes', '1', 'true'] else False
        )
        
        # Preparar registros (solo los primeros 100 para actualización diaria)
        batch_size = 100
        print(f"📤 Preparando {batch_size} registros más recientes...")

        # Convertimos a lista de dicts nativos
        raw_records = df_to_upload.head(batch_size).to_dict(orient="records")

        records = []

        for record in raw_records:
            # Validación mínima
            if not record.get("fecha_iso") or not record.get("hora"):
                continue

            cleaned_record = {
                "fecha": record["fecha_iso"],
                "hora": str(record["hora"]).strip() if record["hora"] else None,
                "latitud": float(record["latitud"]) if pd.notna(record["latitud"]) else None,
                "longitud": float(record["longitud"]) if pd.notna(record["longitud"]) else None,
                "profundidad": str(record["profundidad"]).strip() if record["profundidad"] else None,
                "magnitud": float(record["magnitud"]) if pd.notna(record["magnitud"]) else None,
                "provincia": str(record["provincia"]).strip() if record["provincia"] else None,
                "sentido": bool(record["sentido_bool"])
            }

            records.append(cleaned_record)


        if not records:
            print("⚠️  No hay registros válidos para sincronizar")
            return
        
        import json

        try:
            json.dumps(records)
            print("JSON válido")
        except Exception as e:
            print("Error serializando JSON:", e)

        print(f"🔄 Sincronizando {len(records)} registros con Supabase...")
        
        # Método 1: Intentar upsert con ignoreDuplicates (más moderno)
        try:
            response = supabase.table("sismos").upsert(
                records,
                on_conflict="fecha,hora,latitud,longitud"
            ).execute()
            print(f"✅ Sincronización exitosa: {len(records)} registros procesados")
            
        except Exception as e1:
            # Método 2: Fallback - insertar uno por uno ignorando conflictos
            print(f"⚠️  Upsert masivo falló, intentando inserción individual...")
            print(f"   Error: {str(e1)[:100]}")
            
            success_count = 0
            error_count = 0
            
            for record in records:
                try:
                    # Verificar si existe
                    existing = supabase.table("sismos").select("*").match({
                        "fecha": record["fecha"],
                        "hora": record["hora"],
                        "latitud": record["latitud"],
                        "longitud": record["longitud"]
                    }).execute()
                    
                    if not existing.data:
                        # No existe, insertar
                        supabase.table("sismos").insert(record).execute()
                        success_count += 1
                    else:
                        # Ya existe, actualizar
                        supabase.table("sismos").update(record).match({
                            "fecha": record["fecha"],
                            "hora": record["hora"],
                            "latitud": record["latitud"],
                            "longitud": record["longitud"]
                        }).execute()
                        success_count += 1
                        
                except Exception as e2:
                    error_count += 1
                    if error_count <= 3:  # Mostrar solo primeros 3 errores
                        print(f"   ⚠️  Error en registro: {str(e2)[:80]}")
            
            print(f"✅ Procesados: {success_count} exitosos, {error_count} errores")

    except Exception as e:
        print("=" * 60)
        print("❌ ERROR CRÍTICO AL SINCRONIZAR CON SUPABASE")
        print(f"Detalle: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("=" * 60)
    print("✅ PROCESO FINALIZADO EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    main()