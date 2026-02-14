import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Análisis Sísmico", page_icon="📊", layout="wide")

st.title("📊 Análisis Estadístico Sísmico")

# Reutilizar cargado de datos
GITHUB_CSV_URL = "https://raw.githubusercontent.com/LuisOVaras/inpres-sismos/refs/heads/main/data/sismos.csv"

@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv(GITHUB_CSV_URL)
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y')
    if df['profundidad'].dtype == object:
        df['profundidad'] = df['profundidad'].str.replace(' Km', '', regex=False).astype(float)
    return df

data = load_data()

# Tabs para organización
tab_temp, tab_geo, tab_dist = st.tabs(["🕒 Tendencias Temporales", "🗺️ Distribución por Provincia", "📉 Distribución de Magnitud"])

with tab_temp:
    st.subheader("Evolución de Sismos en el Tiempo")
    
    # Selector de granularidad
    freq = st.selectbox("Agrupar por:", ["Día", "Mes", "Año"], index=1)
    map_freq = {"Día": "D", "Mes": "M", "Año": "Y"}
    
    df_temp = data.set_index('fecha').resample(map_freq[freq]).size().reset_index()
    df_temp.columns = ['fecha', 'cantidad']
    
    fig_line = px.line(df_temp, x='fecha', y='cantidad', 
                       title=f"Cantidad de Sismos por {freq}",
                       template="plotly_white",
                       line_shape="spline")
    st.plotly_chart(fig_line, use_container_width=True)

with tab_geo:
    st.subheader("Sismos por Provincia")
    
    df_prov = data['provincia'].value_counts().reset_index()
    df_prov.columns = ['provincia', 'cantidad']
    
    fig_bar = px.bar(df_prov.head(15), x='cantidad', y='provincia', 
                     orientation='h', 
                     title="Top 15 Provincias con más Sismos",
                     color='cantidad',
                     color_continuous_scale='Reds')
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

with tab_dist:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribución de Magnitudes")
        fig_hist = px.histogram(data, x="magnitud", nbins=20, 
                                title="Histograma de Magnitud",
                                color_discrete_sequence=['indianred'])
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with col2:
        st.subheader("Relación Magnitud vs Profundidad")
        fig_scatter = px.scatter(data, x="magnitud", y="profundidad", 
                                 color="magnitud", 
                                 size="magnitud",
                                 hover_name="provincia",
                                 opacity=0.5,
                                 title="Scatter: Magnitud vs Profundidad")
        st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")
st.info("Utiliza Plotly para interactuar con los gráficos (zoom, pan, hover).")
