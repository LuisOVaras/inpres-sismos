"""
Actualizar sismos - Scraping diario desde INPRES últimos sismos.
Scrapea http://contenidos.inpres.gob.ar/sismologia/xultimos
y prepone los nuevos sismos al archivo sismos.csv
"""
import csv
import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


# ── Configuración ──────────────────────────────────────────────
ULTIMOS_URL = "http://contenidos.inpres.gob.ar/sismologia/xultimos"

# Ruta al CSV principal
OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "sismos.csv"
)
OUTPUT_FILE = os.path.abspath(OUTPUT_FILE)

CURRENT_YEAR = datetime.now().year


def scrape_ultimos(driver):
    """
    Scrapea la tabla de últimos sismos.
    
    La página tiene una estructura vertical especial:
    - Cada columna de datos está en un <div> con id específico
    - Dentro de cada div, hay <p> tags, uno por cada sismo
    - El color #f00 indica que el sismo fue sentido
    
    IDs de los divs:
      - #num: número
      - #dia: fecha (DD/MM)
      - #hora: hora (HH:MM)
      - #la: latitud
      - #lo: longitud
      - #mg: magnitud
      - #prof: profundidad (con " Km")
      - #provincia: provincia (con links)
    """
    sismos = []

    try:
        # Esperar a que la tabla cargue
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "dia"))
        )
    except Exception:
        print("ERROR: No se pudo cargar la tabla de últimos sismos.")
        return sismos

    # Extraer cada columna como lista de textos
    def get_column_data(div_id):
        """Extrae los textos de los <p> dentro del div con el id dado."""
        try:
            div = driver.find_element(By.ID, div_id)
            paragraphs = div.find_elements(By.TAG_NAME, "p")
            return [p.text.strip() for p in paragraphs]
        except Exception:
            return []

    def get_column_colors(div_id):
        """Extrae los colores de los <font> dentro de cada <p> del div."""
        try:
            div = driver.find_element(By.ID, div_id)
            paragraphs = div.find_elements(By.TAG_NAME, "p")
            colors = []
            for p in paragraphs:
                try:
                    font = p.find_element(By.TAG_NAME, "font")
                    color = font.get_attribute("color") or "#000"
                    colors.append(color.lower())
                except Exception:
                    colors.append("#000")
            return colors
        except Exception:
            return []

    def get_provincia_texts(div_id):
        """Extrae los textos de provincia desde los links."""
        try:
            div = driver.find_element(By.ID, div_id)
            paragraphs = div.find_elements(By.TAG_NAME, "p")
            provincias = []
            for p in paragraphs:
                try:
                    link = p.find_element(By.TAG_NAME, "a")
                    font = link.find_element(By.TAG_NAME, "font")
                    provincias.append(font.text.strip())
                except Exception:
                    provincias.append(p.text.strip())
            return provincias
        except Exception:
            return []

    # Extraer columnas
    dias = get_column_data("dia")
    horas = get_column_data("hora")
    latitudes = get_column_data("la")
    longitudes = get_column_data("lo")
    magnitudes = get_column_data("mg")
    profundidades = get_column_data("prof")
    provincias = get_provincia_texts("provincia")
    colores = get_column_colors("num")  # el color del número indica sentido

    # Determinar cuántos sismos hay
    n = min(len(dias), len(horas), len(latitudes), len(longitudes),
            len(magnitudes), len(profundidades), len(provincias))

    if n == 0:
        print("No se encontraron sismos en la página.")
        return sismos

    for i in range(n):
        # Fecha: convertir DD/MM → DD/MM/YYYY
        dia_raw = dias[i]  # ej: "11/02"
        try:
            fecha = f"{dia_raw}/{CURRENT_YEAR}"
        except Exception:
            fecha = dia_raw

        # Hora: agregar :00 para segundos (HH:MM → HH:MM:00)
        hora = f"{horas[i]}:00" if horas[i] else ""

        # Profundidad ya viene con " Km"
        profundidad = profundidades[i]

        # Sentido: basado en el color (#f00 = rojo = sentido)
        sentido = "No"
        if i < len(colores) and colores[i] in ("#f00", "#ff0000", "red"):
            sentido = "Si"

        sismo = {
            "fecha": fecha,
            "hora": hora,
            "latitud": latitudes[i],
            "longitud": longitudes[i],
            "profundidad": profundidad,
            "magnitud": magnitudes[i],
            "provincia": provincias[i],
            "sentido": sentido,
        }
        sismos.append(sismo)

    return sismos


def main():
    print("=" * 60)
    print("INPRES - Actualización diaria de sismos")
    print(f"Fuente: {ULTIMOS_URL}")
    print(f"Destino: {OUTPUT_FILE}")
    print("=" * 60)

    # Configurar Selenium
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    try:
        print("\n[1] Navegando a últimos sismos...")
        driver.get(ULTIMOS_URL)

        print("[2] Scrapeando datos...")
        nuevos_sismos = scrape_ultimos(driver)
        print(f"    Encontrados: {len(nuevos_sismos)} sismos")

    finally:
        driver.quit()

    if not nuevos_sismos:
        print("No se obtuvieron datos nuevos.")
        return

    # Leer CSV existente
    print("[3] Leyendo CSV existente...")
    existing_data = []
    try:
        with open(OUTPUT_FILE, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_data = list(reader)
        print(f"    Datos existentes: {len(existing_data)} registros")
    except FileNotFoundError:
        print("    Archivo no encontrado, se creará uno nuevo.")

    # Crear set de claves únicas para evitar duplicados
    existing_keys = set()
    for row in existing_data:
        key = (row.get("fecha", ""), row.get("hora", ""),
               row.get("latitud", ""), row.get("longitud", ""))
        existing_keys.add(key)

    # Filtrar solo sismos nuevos (no duplicados)
    sismos_nuevos_filtrados = []
    for sismo in nuevos_sismos:
        key = (sismo["fecha"], sismo["hora"],
               sismo["latitud"], sismo["longitud"])
        if key not in existing_keys:
            sismos_nuevos_filtrados.append(sismo)

    print(f"    Sismos nuevos (sin duplicados): {len(sismos_nuevos_filtrados)}")

    if not sismos_nuevos_filtrados:
        print("No hay sismos nuevos para agregar.")
        return

    # Preponer nuevos datos al inicio del CSV
    all_data = sismos_nuevos_filtrados + existing_data

    print(f"[4] Guardando {len(all_data)} registros totales...")
    fieldnames = [
        "fecha", "hora", "latitud", "longitud",
        "profundidad", "magnitud", "provincia", "sentido",
    ]
    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"\n¡Actualización completada!")
    print(f"  Nuevos sismos agregados: {len(sismos_nuevos_filtrados)}")
    print(f"  Total registros: {len(all_data)}")


if __name__ == "__main__":
    main()