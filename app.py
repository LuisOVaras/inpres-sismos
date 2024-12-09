import streamlit as st
import pandas as pd
import sqlite3
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import geopandas as gpd

# Configuración inicial
st.set_page_config(
    page_title="Sismos en Argentina",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Cargar el csv
df_csv = pd.read_csv('data\sismos.csv')
# Título de la página
st.title("📊 Pagina Inicial")

# Menú de navegación
st.sidebar.success("🔍 Navega por las secciones:")
tab1, tab2, tab3, tab4 = st.tabs(['Mapa','datos','datos','datos'])

# Función para cargar datos desde SQLite
@st.cache_data
def load_data():
    conn = sqlite3.connect("data\sismos.db")  
    df = pd.read_sql_query("SELECT * FROM sismos", conn)
    conn.close()
    return df

data = load_data()

# Función para cargar datos como GeoDataFrame
def load_geodata(df):
    if "longitud" in df.columns and "latitud" in df.columns:
        return gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["longitud"], df["latitud"]),
            crs="EPSG:4326",
        )
    else:
        st.warning("No se encontraron columnas de latitud y longitud en los datos.")
        return None


def heat_map(tipoMapa):
    # Conectar a la base de datos SQLite
    conn = sqlite3.connect('data\sismos.db')
    cursor = conn.cursor()

    # Obtener los datos de los sismos actuales
    cursor.execute("SELECT latitud, longitud, magnitud FROM sismos WHERE fecha >= DATE('now', '-30 days')")
    data = cursor.fetchall()

    # Convertir los datos a un DataFrame de pandas
    df = pd.DataFrame(data, columns=['latitud', 'longitud', 'magnitud'])
    

    # Crear el mapa base con el estilo seleccionado y la atribución correspondiente
    mapa = folium.Map(location=[-38.4161, -63.6167], zoom_start=4, tiles=tipoMapa)

    # Agregar el mapa de calor con mayor opacidad (0.5)
    heat_data = [[row['latitud'], row['longitud'], row['magnitud']] for index, row in df.iterrows()]
    HeatMap(heat_data, max_zoom=13, min_opacity=0.2, radius=15, blur=10, gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'}).add_to(mapa)

    # Cerrar la conexión
    conn.close()
    return mapa

with tab1:
    # Mostrar el mapa
    st.markdown("#### A continuación se muestra un mapa de calor de los sismos del último mes: ")
    tipoMapa = st.selectbox('Tipo de Mapa', options=['OpenStreetMap','Cartodb dark_matter', 'Cartodb Positron'])
    
    mapa = heat_map(tipoMapa)
    st_folium(mapa, width=800, height=700)
    
    st.subheader("Sismos del ultimo mes registrados: ")
    
    # Asegúrate de que la columna 'fecha' esté en formato datetime
    data['fecha'] = pd.to_datetime(data['fecha']).dt.date

    # Obtener la fecha actual (sin tiempo) y calcular 30 días atrás
    fecha_hoy = pd.Timestamp.now().date()
    fecha_30_dias = fecha_hoy - pd.Timedelta(days=30)

    # Filtrar el DataFrame
    sub_data = data[data['fecha'] >= fecha_30_dias]

    # Mostrar los resultados
    st.write(f"Datos de los últimos 30 días (desde {fecha_30_dias}):")
    st.dataframe(sub_data, width=800)
