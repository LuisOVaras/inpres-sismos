"""
Actualizar Database SQLite - Sincronización desde CSV
Lee sismos.csv y actualiza la base de datos SQLite sismos.db
Compatible con estructura: inpres_sismos/inpres_sismos/db_scripts/
"""
import pandas as pd
import sqlite3
import os
import sys

# Obtener ruta absoluta con múltiples fallbacks
base_dir = os.path.dirname(os.path.abspath(__file__))

# Path relativo desde db_scripts hacia data (3 niveles arriba)
csv_path = os.path.join(base_dir, '..', '..', '..', 'data', 'sismos.csv')
db_path = os.path.join(base_dir, '..', '..', '..', 'data', 'sismos.db')

# Normalizar paths
csv_path = os.path.normpath(csv_path)
db_path = os.path.normpath(db_path)

print("=" * 60)
print("ACTUALIZACIÓN DE BASE DE DATOS SQLITE")
print("=" * 60)
print(f"📂 CSV: {csv_path}")
print(f"💾 DB: {db_path}")

# Verificar que el CSV existe
if not os.path.exists(csv_path):
    print(f"❌ Error: No se encontró {csv_path}")
    sys.exit(1)

try:
    # Leer el CSV
    sismos_nuevos_df = pd.read_csv(csv_path)
    print(f"📊 Registros en CSV: {len(sismos_nuevos_df)}")

    # Convertir la columna 'fecha' de 'DD/MM/YYYY' a 'YYYY-MM-DD'
    sismos_nuevos_df['fecha'] = pd.to_datetime(
        sismos_nuevos_df['fecha'], 
        format='%d/%m/%Y',
        errors='coerce'
    ).dt.strftime('%Y-%m-%d')
    
    # Convertir la columna 'sentido' a 1 (Sí) o 0 (No)
    sismos_nuevos_df['sentido'] = sismos_nuevos_df['sentido'].apply(
        lambda x: 1 if str(x).strip().lower() in ['si', 'sí', 'yes', '1', 'true'] else 0
    )

    # Crear directorio si no existe
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)

    # Crear la conexión a SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crear la tabla si no existe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sismos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATE,
        hora TIME,
        latitud REAL,
        longitud REAL,
        profundidad TEXT,
        magnitud REAL,
        provincia TEXT,
        sentido INTEGER
    )
    """)

    # Crear índice único para evitar duplicados
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_sismos_unique
    ON sismos (fecha, hora, latitud, longitud)
    """)

    # Revertir el orden para que los más recientes queden al final
    sismos_nuevos_df = sismos_nuevos_df[::-1]

    # Insertar los datos solo si no están ya presentes
    inserted_count = 0
    skipped_count = 0
    
    for index, row in sismos_nuevos_df.iterrows():
        # Skip rows with invalid data
        if pd.isna(row['fecha']) or pd.isna(row['hora']):
            skipped_count += 1
            continue
            
        # Verificar si el registro ya existe en la base de datos
        cursor.execute("""
        SELECT COUNT(*) FROM sismos 
        WHERE fecha = ? AND hora = ? AND latitud = ? AND longitud = ?
        """, (row['fecha'], row['hora'], row['latitud'], row['longitud']))
        
        if cursor.fetchone()[0] == 0:  # Si no existe, insertar
            cursor.execute("""
            INSERT INTO sismos (fecha, hora, latitud, longitud, profundidad, magnitud, provincia, sentido)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['fecha'], 
                row['hora'], 
                row['latitud'], 
                row['longitud'], 
                row['profundidad'], 
                row['magnitud'], 
                row['provincia'], 
                row['sentido']
            ))
            inserted_count += 1
        else:
            skipped_count += 1

    # Confirmar los cambios
    conn.commit()

    # Obtener total de registros
    cursor.execute("SELECT COUNT(*) FROM sismos")
    total = cursor.fetchone()[0]

    # Cerrar la conexión
    conn.close()

    print(f"✅ Insertados: {inserted_count} registros nuevos")
    print(f"ℹ️  Omitidos: {skipped_count} registros (duplicados o inválidos)")
    print(f"📊 Total en DB: {total} registros")
    print("=" * 60)
    print("✅ ACTUALIZACIÓN COMPLETADA")
    print("=" * 60)

except Exception as e:
    print("=" * 60)
    print("❌ ERROR AL ACTUALIZAR DATABASE")
    print(f"Detalle: {e}")
    print("=" * 60)
    import traceback
    traceback.print_exc()
    sys.exit(1)