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
# Título de la página
st.title("📊 Análisis Sísmico")
tab1, tab2, tab3, tab4 = st.tabs(['Tendencias Temporales','Distribución Geográfica','Comparación con Datos Históricos','Top Sismos Recientes'])

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