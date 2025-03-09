import streamlit as st
import pandas as pd
import sqlite3
import geopandas as gpd

# Configuración inicial
st.set_page_config(
    page_title="Sismos en Argentina",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Título de la página
st.title("📢 Información Sísmica")
tab1, tab2, tab3, tab4 = st.tabs(['Escalas de Magnitud','Medidas de Prevención','Terremotos Históricos','Fuentes y Metodología'])
