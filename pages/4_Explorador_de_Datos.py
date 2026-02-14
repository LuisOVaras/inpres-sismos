import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Explorador de Datos", page_icon="📂", layout="wide")

st.title("📂 Explorador y Descarga de Datos")

# Configuración de URLs
GITHUB_CSV_URL = "https://raw.githubusercontent.com/LuisOVaras/inpres-sismos/refs/heads/main/data/sismos.csv"

@st.cache_data(ttl=3600)
def load_data():
    return pd.read_csv(GITHUB_CSV_URL)

df = load_data()

tab1, tab2, tab3 = st.tabs(["🔍 Vista Previa", "📥 Descarga", "🌐 Supabase (Cloud)"])

with tab1:
    st.subheader("Explorador de Registros")
    # Buscador por provincia
    search = st.text_input("Buscar por Provincia o Texto", "")
    if search:
        df_display = df[df.apply(lambda row: search.lower() in row.astype(str).str.lower().values, axis=1)]
    else:
        df_display = df
    
    st.dataframe(df_display.head(500), use_container_width=True)
    st.caption(f"Mostrando {min(len(df_display), 500)} de {len(df_display)} registros.")

with tab2:
    st.subheader("Exportar Datos")
    st.write("Puedes descargar la base de datos completa en formato CSV.")
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar sismos.csv",
        data=csv,
        file_name='sismos_argentina.csv',
        mime='text/csv',
    )
    
    st.write("---")
    st.write("Si necesitas el archivo SQLite (`sismos.db`), puedes encontrarlo en la carpeta `data/` del repositorio.")

with tab3:
    st.subheader("Conexión con Supabase")
    st.markdown("""
    La base de datos en la nube (Supabase) permite consultas SQL en tiempo real y persistencia externa. 
    
    **Estado de la integración:** Configurada en GitHub Actions.
    """)
    
    st.info("""
    Para activar la vista de Supabase aquí, asegúrate de configurar los **Secrets** en Streamlit Cloud:
    - `SUPABASE_URL`
    - `SUPABASE_KEY`
    """)
    
    if st.button("Probar Conexión (Requiere Configuración)"):
        try:
            from supabase import create_client
            # Este bloque solo funcionará si los secrets existen
            url = st.secrets.get("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_KEY")
            if url and key:
                supabase = create_client(url, key)
                st.success("¡Conexión exitosa con Supabase!")
            else:
                st.warning("Credenciales no encontradas en st.secrets")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
st.markdown("© 2026 - Sistema de Monitoreo de Sismos INPRES")
