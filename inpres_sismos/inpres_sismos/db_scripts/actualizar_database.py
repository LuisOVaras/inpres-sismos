import sqlite3
import pandas as pd

# Ruta a la base de datos SQLite
DATABASE_PATH = '..\..\..\data\sismos.db' # ruta donde se encuentra tu db
CSV_PATH = '..\..\..\data\sismos.csv'  # ruta donde se encuentra tu archivo CSV

# Función para conectar a la base de datos SQLite
def conectar_db():
    conn = sqlite3.connect(DATABASE_PATH)
    return conn

# Función para leer el CSV (o los datos de Selenium) y devolver un DataFrame
def leer_datos_csv():
    # Leer el CSV con pandas (ajusta la ruta y parámetros según tu archivo)
    df = pd.read_csv(CSV_PATH, parse_dates=['fecha'])
    return df

# Función para insertar datos en la base de datos
def insertar_datos_en_db(df):
    conn = conectar_db()
    cursor = conn.cursor()

    # Insertar datos fila por fila
    for index, row in df.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO sismos (fecha, hora, latitud, longitud, profundidad, magnitud, provincia, sentido)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (row['fecha'], row['hora'], row['latitud'], row['longitud'], row['profundidad'], row['magnitud'], row['provincia'], row['sentido']))
    
    # Commit para guardar los cambios y cerrar la conexión
    conn.commit()
    conn.close()

# Main: ejecutar las funciones
if __name__ == "__main__":
    # Leer los nuevos datos desde el CSV (o donde sea que los tengas)
    df_nuevos_datos = leer_datos_csv()
    
    # Insertar esos datos en la base de datos
    insertar_datos_en_db(df_nuevos_datos)
    
    print("Base de datos actualizada con los nuevos datos.")
