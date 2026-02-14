import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuración inicial - Premium Design
st.set_page_config(
    page_title="Argentina Sismos - Dashboard",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado para aspecto Premium
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# URL del CSV en tu repositorio de GitHub
GITHUB_CSV_URL = "https://raw.githubusercontent.com/LuisOVaras/inpres-sismos/refs/heads/main/data/sismos.csv"

@st.cache_data(ttl=3600)
def load_data():
    try:
        # Intentar cargar desde CSV (GitHub)
        df = pd.read_csv(GITHUB_CSV_URL)
        df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y').dt.date
        df["hora"] = pd.to_datetime(df["hora"], format='%H:%M:%S', errors="coerce").dt.time
        
        # Limpieza de profundidad
        if df['profundidad'].dtype == object:
            df['profundidad'] = df['profundidad'].str.replace(' Km', '', regex=False).astype(float)
        
        cols_a_convertir = ["magnitud", "latitud", "longitud"]
        df[cols_a_convertir] = df[cols_a_convertir].apply(pd.to_numeric, errors="coerce")

        return df.dropna(subset=["latitud", "longitud", 'provincia'])
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()

# Cargar los datos
data = load_data()

if data.empty:
    st.warning("No se pudieron cargar los datos. Verifica la conexión.")
    st.stop()

# --- SIDEBAR FILTROS ---
st.sidebar.image("https://www.inpres.gob.ar/desktop/img/logo_inpres.png", width=200)
st.sidebar.title("Filtros Globales")

# Rango de fechas
fecha_max = data['fecha'].max()
fecha_min = data['fecha'].min()
rango_default = (fecha_max - timedelta(days=30), fecha_max)

fecha_rango = st.sidebar.date_input(
    "Rango de Fechas",
    value=rango_default,
    min_value=fecha_min,
    max_value=fecha_max
)

# Magnitud Slider
magnitud_range = st.sidebar.slider(
    "Magnitud (Mw)",
    min_value=float(data['magnitud'].min()),
    max_value=float(data['magnitud'].max()),
    value=(2.0, 9.0),
    step=0.1
)

# Provincia multiselect
provincias = sorted(data['provincia'].unique().tolist())
prov_sel = st.sidebar.multiselect("Provincias", provincias, default=[])

# Aplicar Filtros
mask = (data['fecha'] >= fecha_rango[0]) & (data['fecha'] <= fecha_rango[1]) & \
       (data['magnitud'] >= magnitud_range[0]) & (data['magnitud'] <= magnitud_range[1])

if prov_sel:
    mask = mask & (data['provincia'].isin(prov_sel))

df_filtered = data[mask]

# --- MAIN LAYOUT ---
st.title("🌋 Monitoreo Sísmico Argentina")
st.markdown("Dashboard interactivo con datos en tiempo real de INPRES.")

# Métricas Principales
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Sismos", len(df_filtered))
with col2:
    st.metric("Max Magnitud", f"{df_filtered['magnitud'].max():.1f}")
with col3:
    st.metric("Profundidad Media", f"{df_filtered['profundidad'].mean():.0f} km")
with col4:
    last_date = df_filtered['fecha'].max()
    st.metric("Último Registro", last_date.strftime('%d/%m/%Y') if not df_filtered.empty else "N/A")

# Mapa Interactivo con Plotly
st.subheader("📍 Mapa de Localizaciones")

if not df_filtered.empty:
    fig_map = px.scatter_mapbox(
        df_filtered,
        lat="latitud",
        lon="longitud",
        size="magnitud",
        color="magnitud",
        color_continuous_scale=px.colors.sequential.YlOrRd,
        hover_name="provincia",
        hover_data=["fecha", "hora", "profundidad", "magnitud"],
        zoom=3.5,
        center={"lat": -38.4161, "lon": -63.6167},
        height=600,
        mapbox_style="carto-positron"
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("No hay datos para los filtros seleccionados.")

# Tabla de Datos Recientes
st.subheader("📋 Registros Filtrados")
st.dataframe(df_filtered.head(100), use_container_width=True)

st.markdown("---")
st.caption("Datos obtenidos automáticamente de INPRES Argentina.")
