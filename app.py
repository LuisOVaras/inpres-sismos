import streamlit as st
import pandas as pd
import sqlite3
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
import geopandas as gpd
import urllib.request

# Configuración inicial
st.set_page_config(
    page_title="Sismos en Argentina",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL del CSV en tu repositorio de GitHub
GITHUB_CSV_URL = "https://raw.githubusercontent.com/LuisOVaras/inpres-sismos/refs/heads/main/data/sismos.csv"

# URL del archivo SQLite en GitHub
GITHUB_DB_URL = "https://github.com/LuisOVaras/inpres-sismos/raw/refs/heads/main/data/sismos.db"
DB_FILE = "sismos.db"

@st.cache_data(ttl=3600)
def descargar_db():
    urllib.request.urlretrieve(GITHUB_DB_URL, DB_FILE)  # Descargar la base de datos

descargar_db()  # Descargar la base de datos antes de abrirla

def load_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM sismos", conn)
    conn.close()
    return df

data = load_data()

# Título de la página
st.title("🌍 Visualización de Sismos")
tab1, tab2, tab3, tab4 = st.tabs(['Mapa de calor','Mapa de Sismos','Mapa con Clusters','Estadísticas básicas'])


# Todos lod filtros para la pagina 1
# Sidebar: Selección de rango de fechas
st.sidebar.header("Filtros: ")

    # Asegurar que la columna 'fecha' esté en formato datetime
data['fecha'] = pd.to_datetime(data['fecha']).dt.date
    
    # Limpiar y convertir la columna 'profundidad' a float
data['profundidad'] = data['profundidad'].str.replace(' Km', '', regex=False)  # Quitar ' Km'
data['profundidad'] = pd.to_numeric(data['profundidad'], errors='coerce')  # Convertir a número
    
    # Eliminar filas con NaN en 'profundidad' si existen
data = data.dropna(subset=['profundidad'])
    # Redondea los valores a enteros y luego convierte a tipo 'int'
data['profundidad'] = data['profundidad'].round().astype('int')


    # Obtener la fecha mínima y máxima en los datos
fecha_min = data['fecha'].min()
fecha_max = data['fecha'].max()
    
    # Selector de fechas en el sidebar
fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Selecciona el rango de fechas",
    [fecha_max - pd.Timedelta(days=30), fecha_max],  # Últimos 30 días por defecto
    min_value=fecha_min,
    max_value=fecha_max
)

    # Filtrar el DataFrame según el rango de fechas
sub_data = data[(data['fecha'] >= fecha_inicio) & (data['fecha'] <= fecha_fin)]
    
    # Ordenar los datos de forma descendente por fecha
sub_data = sub_data.sort_values(by='fecha', ascending=False)
sub_data = sub_data.set_index('id')
    
    # Obtener la fecha mínima y máxima en los datos
magnitud_min = float(sub_data['magnitud'].min())
magnitud_max  = float(sub_data['magnitud'].max())

     # Selector de fechas en el sidebar
magnitud = st.sidebar.slider(
    "Selecciona el rango de magnitud: ",
    min_value=magnitud_min,
    max_value=magnitud_max,
    value=(magnitud_min, magnitud_max)
)
    # Filtrar por magnitud
sub_data = sub_data[(sub_data['magnitud'] >= magnitud[0]) & (sub_data['magnitud'] <= magnitud[1])]
    
if 'profundidad' in sub_data.columns:
    profundidad_min = float(sub_data['profundidad'].min())
    profundidad_max = float(sub_data['profundidad'].max())

    profundidad = st.sidebar.slider("Selecciona el rango de profundidad (km):", 
                                    min_value=profundidad_min, max_value=profundidad_max, 
                                    value=(profundidad_min, profundidad_max))

# 📍 FILTRO POR UBICACIÓN (EJEMPLO CON PROVINCIAS)
if 'provincia' in sub_data.columns:
    provincias = sub_data['provincia'].unique().tolist()
    provincia_seleccionada = st.sidebar.multiselect("Filtrar por provincia:", provincias, default=provincias)

    
    # Filtrar por profundidad (si existe)
if 'profundidad' in sub_data.columns:
    sub_data = sub_data[(sub_data['profundidad'] >= profundidad[0]) & (sub_data['profundidad'] <= profundidad[1])]

    # Filtrar por provincia (si existe la columna)
if 'provincia' in sub_data.columns:
    sub_data = sub_data[sub_data['provincia'].isin(provincia_seleccionada)]


# Convertir los datos a un DataFrame de pandas
df = pd.DataFrame(sub_data, columns=['latitud', 'longitud', 'magnitud','fecha','profundidad', 'provincia','sentido' ])


def heat_map(tipoMapa):
    # Crear el mapa base con el estilo seleccionado
    mapa = folium.Map(location=[-38, -65], zoom_start=4, tiles=tipoMapa)

    # Verificar que hay datos antes de crear el heatmap
    if not df.empty:
        heat_data = [[row['latitud'], row['longitud'], row['magnitud']] for index, row in df.iterrows()]
        HeatMap(heat_data, max_zoom=13, min_opacity=0.2, radius=15, blur=10, 
                gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'}).add_to(mapa)

    return mapa

def circlemarker_map(tipoMapa):

    # Crear mapa base
    mapa = folium.Map(location=[-38, -65], zoom_start=4, tiles=tipoMapa)

    
    # Agregar puntos individuales
    for _, row in df.iterrows():
        popup_info = f"""
        <b>Fecha:</b> {row['fecha']}<br>
        <b>Magnitud:</b> {row['magnitud']}<br>
        <b>Profundidad:</b> {row['profundidad']} km <br>
        <b>Sentido:</b> {"Sí" if row['sentido'] == 1 else "No"}
        """
        folium.CircleMarker(
            location=[row["latitud"], row["longitud"]],
            radius=row["magnitud"] * 2,  # Ajusta el tamaño según la magnitud
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.6,
            popup=folium.Popup(popup_info, max_width=300)
        ).add_to(mapa)

    return mapa

with tab1:
    # Título y descripción
    st.markdown("#### A continuación se muestra un mapa de calor de los sismos del último mes: ")

    # Mostrar mapa con opción de tipo de mapa
    tipoMapa = st.selectbox('Tipo de Mapa', options=['OpenStreetMap', 'Cartodb dark_matter', 'Cartodb Positron'])
    mapa = heat_map(tipoMapa)
    st_folium(mapa, width=800, height=700)

    # Mostrar los datos filtrados
    st.subheader("Sismos registrados en el período seleccionado:")
    sub_data = sub_data.style.format({'magnitud': '{:.1f}', 'latitud': '{:.3f}', 'longitud': '{:.3f}'})
    st.write(f"Datos entre **{fecha_inicio}** y **{fecha_fin}**:")
    st.dataframe(sub_data, width=800)
    
with tab2:
    # Título y descripción
    st.markdown("#### A continuación se muestra un mapa de puntos de los sismos del último mes: ")
    
    # Mostrar mapa con opción de tipo de mapa
    tipoMapa = st.selectbox('Tipo de Mapa', options=['OpenStreetMap', 'Cartodb dark_matter', 'Cartodb Positron'], key = "count")
    mapa = circlemarker_map(tipoMapa)
    st_folium(mapa, width=800, height=700)