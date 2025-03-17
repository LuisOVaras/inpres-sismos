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
def load_data():
    try:
        df = pd.read_csv(GITHUB_CSV_URL)
        df['fecha'] = pd.to_datetime(df['fecha']).dt.date  # Convertir fecha a datetime.date
        df["hora"] = pd.to_datetime(df["hora"], format='%H:%M:%S', errors="coerce").dt.time  # Convertir a time
        df['profundidad'] = df['profundidad'].str.replace(' Km', '', regex=False).astype(float)  # Convertir profundidad
        df["magnitud"] = pd.to_numeric(df["magnitud"], errors="coerce")  # Convertir a numérico
        df["latitud"] = pd.to_numeric(df["latitud"], errors="coerce")  # Convertir a numérico
        df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")  # Convertir a numérico
        return df.dropna(subset=["latitud", "longitud"])  # Eliminar filas sin coordenadas
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()  # Retornar DF vacío en caso de error

# Cargar los datos desde el CSV
data = load_data()

# Si no hay datos, mostrar mensaje y detener ejecución
if data.empty:
    st.warning("No se pudieron cargar los datos de sismos. Intenta más tarde.")
    st.stop()
    
# Título de la página
st.title("🌍 Visualización de Sismos")
# Sidebar para seleccionar la pestaña activa
tab_seleccionada = st.sidebar.selectbox(
    "Selecciona una vista",
    ['Mapa de calor', 'Mapa de Puntos', 'Mapa con Clusters', 'Estadísticas básicas']
)
    
    
# Todos lod filtros para la pagina 1
# Sidebar: Selección de rango de fechas
st.sidebar.header("Filtros: ")
st.sidebar.markdown("**¡Atención!** Para mapas se recomienda seleccionar un rango de fechas no mayor a 6 meses debido a la carga de datos.")

    # Colocar fecha min y max
fecha_min = data['fecha'].min()
fecha_max = data['fecha'].max()

fecha_predeterminada = [fecha_max - pd.Timedelta(days=30), fecha_max]
    # Selector de fechas en el sidebar
fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Selecciona el rango de fechas",
    fecha_predeterminada,  # Últimos 30 días por defecto
    min_value=fecha_min,
    max_value=fecha_max
)

    # Redondea los valores a enteros y luego convierte a tipo 'int'
data['profundidad'] = data['profundidad'].round().astype('int')

# Combinar las columnas de fecha y hora en una columna datetime
data['fecha_hora'] = pd.to_datetime(data['fecha']) + pd.to_timedelta(data['hora'].astype(str))

# Ordenar por la columna 'fecha_hora'
data = data.sort_values(by='fecha_hora', ascending=False)
# Eliminar la columna 'fecha_hora' del DataFrame final
data = data.drop(columns=['fecha_hora'])

    # Filtrar el DataFrame según el rango de fechas
sub_data = data[(data['fecha'] >= fecha_inicio) & (data['fecha'] <= fecha_fin)]
    
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

def markercluster_map(tipoMapa):
    # Crear el mapa base con el estilo seleccionado
    mapa = folium.Map(location=[-38, -65], zoom_start=4, tiles=tipoMapa)

    # Agregar clusters
    marker_cluster = MarkerCluster().add_to(mapa)
    for _, row in df.iterrows():
        folium.Marker(
            location=[row["latitud"], row["longitud"]],
            popup=f"<b>Magnitud:</b>{row['magnitud']}<br><b>Fecha:</b>{row['fecha']}<br><b>Profundidad:</b>{row['profundidad']}Km<br>",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(marker_cluster)

    return mapa

def estadisticas_basicas(sub_data):
            
                # Calcular estadísticas rápidas
    total_sismos = sub_data.shape[0]  # Número total de sismos en el rango seleccionado
    promedio_magnitud = sub_data['magnitud'].mean()  # Promedio de magnitud
    profundidad_media = sub_data['profundidad'].mean()  # Profundidad promedio

            # Usar columnas para mostrar los metrics uno al lado del otro
    col1, col2, col3 = st.columns(3)

            # Mostrar las estadísticas en la tab
    st.subheader("Estadísticas generales")
            # Mostrar las métricas en las columnas
    with col1:
        st.metric("Número total de sismos", total_sismos)

    with col2:
        st.metric("Magnitud promedio", f"{promedio_magnitud:.2f}")

    with col3:
        st.metric("Profundidad media", f"{profundidad_media:.2f} km")
        
# Tabs
if tab_seleccionada == 'Mapa de calor':
    st.write("Cargando Mapa de Calor...")
        # Título y descripción
    st.markdown("#### A continuación se muestra un mapa de calor de los sismos del último mes: ")
        # Mostrar mapa con opción de tipo de mapa
    tipoMapa = st.selectbox('Tipo de Mapa', options=['OpenStreetMap', 'Cartodb dark_matter', 'Cartodb Positron'])
    mapa = heat_map(tipoMapa)
    st_folium(mapa, width=800, height=700)

        # Mostrar los datos filtrados
    pd.set_option("styler.render.max_elements", 600000)
    st.subheader("Sismos registrados en el período seleccionado:")
    sub_data = sub_data.style.format({'magnitud': '{:.1f}', 'latitud': '{:.3f}', 'longitud': '{:.3f}'})
    st.write(f"Datos entre **{fecha_inicio}** y **{fecha_fin}**:")
    st.dataframe(sub_data, width=800)

elif tab_seleccionada == 'Mapa de Puntos':
    st.write("Cargando Mapa de Puntos...")
        # Título y descripción
    st.markdown("#### A continuación se muestra un mapa de puntos de los sismos del último mes: ")
            
        # Mostrar mapa con opción de tipo de mapa
    tipoMapa = st.selectbox('Tipo de Mapa', options=['OpenStreetMap', 'Cartodb dark_matter', 'Cartodb Positron'], key = "tab2")
    mapa = circlemarker_map(tipoMapa)
    st_folium(mapa, width=800, height=700)

elif tab_seleccionada == 'Mapa con Clusters':
    st.write("Cargando Mapa con Clusters...")
        # Título y descripción
    st.markdown("#### A continuación se muestra un mapa de puntos de los sismos del último mes: ")
            
        # Mostrar mapa con opción de tipo de mapa
    tipoMapa = st.selectbox('Tipo de Mapa', options=['OpenStreetMap', 'Cartodb dark_matter', 'Cartodb Positron'], key = "tab3")
    mapa = markercluster_map(tipoMapa)
    st_folium(mapa, width=800, height=700)

elif tab_seleccionada == 'Estadísticas básicas':
    st.write("Cargando Estadísticas básicas...")

        # Mostrar título de la tab
    st.title("Estadísticas Rápidas de los Sismos")

        # Pasar los datos ya filtrados a la función
    estadisticas_basicas(sub_data)
            
    pd.set_option("styler.render.max_elements", 700000)
        # Mostrar los datos filtrados
    st.subheader("Sismos registrados en el período seleccionado:")
    sub_data = sub_data.style.format({'magnitud': '{:.1f}', 'latitud': '{:.3f}', 'longitud': '{:.3f}'})
    st.write(f"Datos entre **{fecha_inicio}** y **{fecha_fin}**:")
    st.dataframe(sub_data, width=800)
    
    
st.markdown("---")  # Línea divisoria
st.markdown("📌 **Para más información sobre los sismos en Argentina, visita:** [INPRES](https://www.inpres.gob.ar)")
