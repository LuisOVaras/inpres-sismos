import streamlit as st
import pandas as pd
import sqlite3


# Configuración inicial
st.set_page_config(
    page_title="Sismos en Argentina",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título de la página
st.title("📂 Explorador de Datos")
tab1, tab2, tab3, tab4 = st.tabs(['Base de Datos','Descargar Datos','Última Actualización','Consultas SQL Personalizadas'])
