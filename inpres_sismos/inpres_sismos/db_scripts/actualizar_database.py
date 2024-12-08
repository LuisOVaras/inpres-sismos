import pandas as pd
import sqlite3
import os

# Obtener la ruta absoluta de la ubicación actual del archivo
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, '..', '..', '..', 'data', 'sismos.csv')
db_path = os.path.join(base_dir, '..', '..', '..', 'data', 'sismos.db')

# Leer el CSV con los datos nuevos (asumo que ya tienes los nuevos datos listos en 'sismos_nuevos.csv')
sismos_nuevos_df = pd.read_csv(csv_path)

# Convertir la columna 'fecha' de 'DD/MM/YYYY' a 'YYYY-MM-DD'
sismos_nuevos_df['fecha'] = pd.to_datetime(sismos_nuevos_df['fecha'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
# Convertir la columna 'sentido' a 1 (Sí) o 0 (No)
sismos_nuevos_df['sentido'] = sismos_nuevos_df['sentido'].apply(lambda x: 1 if x == 'Si' else 0)

# Crear la conexión a SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Revertir el orden de los datos nuevos para que los más recientes queden al final
sismos_nuevos_df = sismos_nuevos_df[::-1]  # Invertir el DataFrame si es necesario

# Insertar los datos solo si no están ya presentes (comparación por fecha, hora, latitud, longitud)
for index, row in sismos_nuevos_df.iterrows():
    # Verificar si el registro ya existe en la base de datos
    cursor.execute("""
    SELECT COUNT(*) FROM sismos WHERE fecha = ? AND hora = ? AND latitud = ? AND longitud = ?
    """, (row['fecha'], row['hora'], row['latitud'], row['longitud']))
    
    if cursor.fetchone()[0] == 0:  # Si no existe, insertar
        cursor.execute("""
        INSERT INTO sismos (fecha, hora, latitud, longitud, profundidad, magnitud, provincia, sentido)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (row['fecha'], row['hora'], row['latitud'], row['longitud'], row['profundidad'], row['magnitud'], row['provincia'], row['sentido']))

# Confirmar los cambios
conn.commit()

# Cerrar la conexión
conn.close()
