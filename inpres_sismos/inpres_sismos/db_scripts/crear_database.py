import pandas as pd
import sqlite3

# Leer el CSV
sismos_df = pd.read_csv("..\..\..\data\sismos.csv")

# Convertir la columna 'fecha' de 'DD/MM/YYYY' a 'YYYY-MM-DD'
sismos_df['fecha'] = pd.to_datetime(sismos_df['fecha'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
# Convertir la columna 'sentido' a 1 (Sí) o 0 (No)
sismos_df['sentido'] = sismos_df['sentido'].apply(lambda x: 1 if x == 'Si' else 0)

# Crear la conexión a SQLite
conn = sqlite3.connect("..\..\..\data\sismos.db")
cursor = conn.cursor()

# Crear la tabla para los datos de sismos
cursor.execute("""
CREATE TABLE IF NOT EXISTS sismos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE,
    hora TIME,
    latitud REAL,
    longitud REAL,
    profundidad REAL,
    magnitud REAL,
    provincia TEXT,
    sentido INTEGER
    
)
""")

# Poblar la tabla desde un archivo CSV
# Insertar los datos en la tabla
for index, row in sismos_df.iterrows():
    cursor.execute("""
    INSERT INTO sismos (fecha, hora, latitud, longitud, profundidad, magnitud, provincia, sentido)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (row['fecha'], row['hora'], row['latitud'], row['longitud'], row['profundidad'], row['magnitud'], row['provincia'], row['sentido']))
    
# Leer el archivo CSV
df_historicos = pd.read_csv('..\..\..\data\sismos_historicos.csv')

# Convertir la columna 'fecha' de 'DD/MM/YYYY' a 'YYYY-MM-DD'
df_historicos['fecha'] = pd.to_datetime(df_historicos['fecha'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')

# Crear la tabla para los sismos históricos si no existe
cursor.execute("""
CREATE TABLE IF NOT EXISTS sismos_historicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE,
    provincia TEXT,
    descripcion TEXT,
    latitud REAL,
    longitud REAL
)
""")

# Insertar los datos de los terremotos históricos
for index, row in df_historicos.iterrows():
    cursor.execute("""
    INSERT INTO sismos_historicos (fecha, provincia, descripcion, latitud, longitud)
    VALUES (?, ?, ?, ?, ?)
    """, (row['fecha'], row['provincia'], row['descripcion'], row['latitud'], row['longitud']))


# Confirmar los cambios
conn.commit()
conn.close()
