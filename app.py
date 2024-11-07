import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Función para cargar los datos de sismos
def load_data():
    # Cargar datos desde un archivo CSV
    df = pd.read_csv('sismos.csv')  # Reemplaza con tu ruta o fuente de datos
    return df

# Mostrar datos históricos
def display_historical_data():
    df = load_data()
    st.subheader('Datos Históricos de Sismos')
    st.write(df)

    # Mostrar visualización de GeoPandas
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitud, df.latitud))
    gdf.plot()
    plt.title('Ubicación de los Sismos')
    st.pyplot()

# Botón para actualizar los datos
if st.button('Actualizar Datos'):
    # Ejecutar el scraping (puedes llamar el spider aquí o usar subprocess para ejecutarlo)
    import subprocess
    subprocess.call(['scrapy', 'crawl', 'sismos'])
    st.success('Datos actualizados correctamente')

# Mostrar los datos históricos
display_historical_data()

# Mostrar los sismos actuales (puedes agregar aquí más lógica según lo necesites)
st.subheader('Sismos Actuales')
current_data = load_data()  # Aquí deberías filtrar los sismos más recientes
st.write(current_data)
