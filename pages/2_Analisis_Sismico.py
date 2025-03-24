import streamlit as st
import pandas as pd
import sqlite3
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import geopandas as gpd
import unidecode

# Configuración inicial
st.set_page_config(
    page_title="Sismos en Argentina",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Título de la página
st.title("📊 Análisis Sísmico")
tab1, tab2, tab3, tab4 = st.tabs(['Tendencias Temporales','Distribución Geográfica','Comparación con Datos Históricos','Top Sismos Recientes'])

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
        cols_a_convertir = ["magnitud", "latitud", "longitud"]
        df[cols_a_convertir] = df[cols_a_convertir].apply(pd.to_numeric, errors="coerce")

        return df.dropna(subset=["latitud", "longitud", 'provincia'])  # Eliminar filas sin coordenadas
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()  # Retornar DF vacío en caso de error

# Cargar los datos desde el CSV
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
    
data = load_data()




# Lista de nombres incorrectos o variantes que deben ser asignados a 'TIERRA DEL FUEGO'
variaciones_tdf = [
    "PASAJES DE DRAKE", "IS. SHETLAND DEL SUR", "ISLAS SANDWICH DEL SUR", "ISLAS GIORGIA Y SANDWICH DEL SUR",
    "ISLAS GEORGIAS Y SANDWICH DEL SUR", "ISLAS GEORGIAS DEL SUR", "ISLAS ORCADAS DEL SUR", "MAR DE SCOTIA",
    "ISLAS GEORGIA DEL SUR", "ISLAS GEORGIAS y SANDWICH DEL SUR", "ISLAS SHETLAND DEL SUR", "ESTRECHO DE DRAKE",
    "ANTARTIDA", "ISLAS SHETLAND", "ISLAS ORCADAS", "ISLAS SANDWICH", "I.SANDWICH DEL SUR", "ATLANTICO SUR",
    "PENINSULA ANTARTICA", "SECTOR ANTARTICO", "TFAIAS", "TFAIAS.", "OCEANO ATLANTICO SUR"
]

# Función para normalizar y asignar 'TIERRA DEL FUEGO' a las variaciones
def normalizar_provincia_sismo(nombre):
    # Convertir a mayúsculas y eliminar acentos
    nombre_normalizado = unidecode.unidecode(nombre.strip().upper())
    
    # Si el nombre está en la lista de variaciones, lo cambiamos a 'TIERRA DEL FUEGO'
    if nombre_normalizado in [unidecode.unidecode(variacion.upper()) for variacion in variaciones_tdf]:
        return 'TIERRA DEL FUEGO'
    return nombre_normalizado
# Función para normalizar los nombres de provincias (quitar acentos y convertir a mayúsculas)
def normalizar_nombre_provincia(nombre):
    nombre = nombre.replace("Tierra del Fuego, Antártida e Islas del Atlántico Sur", "TIERRA DEL FUEGO")  # Reemplazar el nombre largo
    nombre = unidecode.unidecode(nombre.strip().upper())  # Eliminar acentos y convertir a mayúsculas
    return nombre


with tab1:
    # Asegúrate de que la columna 'fecha' sea de tipo datetime
    data['fecha'] = pd.to_datetime(data['fecha'])

    # Agrupar por día
    sismos_por_dia = data.groupby('fecha').size()

    # Graficar
    st.subheader("Sismos por Día")
    st.line_chart(sismos_por_dia)

    # Resample por mes
    sismos_por_mes = sismos_por_dia.resample('M').sum()

    # Graficar
    st.subheader("Sismos por Mes")
    st.line_chart(sismos_por_mes)

    # Resample por año
    sismos_por_ano = sismos_por_dia.resample('Y').sum()

    # Graficar
    st.subheader("Sismos por Año")
    st.line_chart(sismos_por_ano)

with tab2:
    
    
    # Aplicar la normalización en los nombres de las provincias de los sismos
    data['provincia_normalizada'] = data['provincia'].apply(normalizar_provincia_sismo)
    
    # Cargar el shapefile de provincias
    provincias = gpd.read_file("data\provincia\provincia.shp")
    # Normalizar los nombres de las provincias en el GeoDataFrame (column 'nam')
    provincias['nombre_normalizado'] = provincias['nam'].apply(normalizar_nombre_provincia)

    # Agrupar los sismos por provincia (contar el número de registros por provincia)
    sismos_por_provincia = data.groupby('provincia_normalizada').size()

    # Asegurarse de que la Series tiene un nombre para unirla con el GeoDataFrame
    sismos_por_provincia.name = 'sismos'

    # Normalizar los nombres de provincias en el DataFrame de sismos (para que coincidan)
    data['provincia_normalizada'] = data['provincia'].apply(normalizar_nombre_provincia)

    # Unir los datos de sismos con el GeoDataFrame usando la columna 'nombre_normalizado'
    provincias = provincias.set_index('nombre_normalizado').join(sismos_por_provincia, on='nombre_normalizado')

    # Verificar si la columna de sismos está presente
    if 'sismos' not in provincias.columns:
        st.error("No se encontraron datos de sismos por provincia.")
    else:
        # Agregar un filtro para que el usuario seleccione las provincias a mostrar
        provincias_disponibles = provincias.index.tolist()  # Obtener la lista de provincias
        provincias_seleccionadas = st.sidebar.multiselect(
            'Selecciona las provincias a mostrar en el mapa:',
            provincias_disponibles,
            default=provincias_disponibles  # Mostrar todas las provincias por defecto
        )

        # Filtrar el GeoDataFrame para mostrar solo las provincias seleccionadas
        provincias_filtradas = provincias[provincias.index.isin(provincias_seleccionadas)]

        if not provincias_filtradas.empty:
            # Crear el mapa con las provincias seleccionadas
            ax = provincias_filtradas.plot(
                column='sismos', 
                cmap='Oranges',  # Colormap más intensos
                legend=True, 
                figsize=(10, 10),
                edgecolor='black',  # Bordes negros entre provincias
                linewidth=0.2  # Grosor del borde
            )

            # Títulos y leyenda
            ax.set_title("Distribución de Sismos por Provincia", fontsize=15)
            ax.set_axis_off()  # Desactivar los ejes para que el mapa sea más limpio

            # Mostrar el gráfico
            st.pyplot(ax.get_figure())
        else:
            st.warning("No se han seleccionado provincias.")

