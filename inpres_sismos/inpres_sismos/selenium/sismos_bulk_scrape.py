"""
Bulk scraper para INPRES - contenidos.inpres.gob.ar/buscar_sismo
Scrapea sismos desde 09/09/2025 hasta la fecha actual,
dividiendo en rangos de 20 dias para evitar el limite de 500 resultados.
Vuelve al formulario con "Realizar otra busqueda" entre cada rango.
Guarda los resultados acumulados en data/sismos_nuevos.csv
"""
import time
import csv
import os
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager


# -- Configuracion --
SEARCH_URL = "http://contenidos.inpres.gob.ar/buscar_sismo"
FECHA_INICIO_GLOBAL = datetime(2025, 9, 9)
FECHA_FIN_GLOBAL = datetime.now()
DIAS_POR_RANGO = 20  # dias por cada busqueda

# Ruta al CSV de salida
carpeta_data = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
)
OUTPUT_FILE = os.path.join(carpeta_data, "sismos_nuevos.csv")


# -- Funciones auxiliares --

def set_date_input(driver, element_id, date_value):
    """Establece un valor en un input type=date usando JavaScript."""
    script = """
        var input = document.getElementById(arguments[0]);
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        nativeInputValueSetter.call(input, arguments[1]);
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    """
    driver.execute_script(script, element_id, date_value)


def parse_row(row):
    """
    Parsea una fila <tr> de la tabla de resultados.
    Columnas: #, datetime, lat, lon, depth, mag, intensity, province
    """
    cells = row.find_elements(By.TAG_NAME, "td")
    if len(cells) < 8:
        return None

    datetime_str = cells[1].text.strip()
    latitud = cells[2].text.strip()
    longitud = cells[3].text.strip()
    profundidad_raw = cells[4].text.strip()
    magnitud = cells[5].text.strip()
    intensidad = cells[6].text.strip()

    try:
        provincia = cells[7].find_element(By.TAG_NAME, "a").text.strip()
    except NoSuchElementException:
        provincia = cells[7].text.strip()

    # Transformaciones al formato CSV
    try:
        dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        fecha = dt.strftime("%d/%m/%Y")
        hora = dt.strftime("%H:%M:%S")
    except ValueError:
        fecha = datetime_str
        hora = ""

    profundidad = f"{profundidad_raw} Km" if profundidad_raw else ""
    sentido = "Si" if intensidad else "No"

    return {
        "fecha": fecha,
        "hora": hora,
        "latitud": latitud,
        "longitud": longitud,
        "profundidad": profundidad,
        "magnitud": magnitud,
        "provincia": provincia,
        "sentido": sentido,
    }


def scrape_current_page(driver):
    """Scrapea todas las filas de la pagina actual de resultados."""
    results = []
    try:
        tbody = driver.find_element(By.CSS_SELECTOR, "#tableFiltro tbody")
        rows = tbody.find_elements(By.TAG_NAME, "tr")
    except NoSuchElementException:
        return results

    for row in rows:
        try:
            data = parse_row(row)
            if data:
                results.append(data)
        except StaleElementReferenceException:
            continue
        except Exception as e:
            print(f"  Error al procesar fila: {e}")
            continue

    return results


def click_next_page(driver):
    """Intenta hacer clic en 'Siguiente'. Retorna True si habia mas paginas."""
    try:
        next_li = driver.find_element(By.ID, "tableFiltro_next")
        if "disabled" in next_li.get_attribute("class"):
            return False
        next_link = next_li.find_element(By.TAG_NAME, "a")
        next_link.click()
        return True
    except NoSuchElementException:
        return False


def fill_form_and_search(driver, fecha_inicio_str, fecha_fin_str):
    """Llena el formulario de busqueda y hace clic en Buscar."""
    # Fecha inicio
    set_date_input(driver, "datepicker", fecha_inicio_str)
    time.sleep(0.5)

    # Fecha fin
    set_date_input(driver, "datepicker2", fecha_fin_str)
    time.sleep(0.5)

    # Checkbox tilde1
    checkbox = driver.find_element(By.NAME, "tilde1")
    if not checkbox.is_selected():
        checkbox.click()
    time.sleep(0.5)

    # Click en Buscar
    buscar_btn = driver.find_element(
        By.CSS_SELECTOR, "button.btn.btn-success[type='submit']"
    )
    buscar_btn.click()


def scrape_all_pages(driver):
    """Scrapea todas las paginas de resultados de la busqueda actual."""
    data = []
    page = 0

    while True:
        page += 1
        page_data = scrape_current_page(driver)
        data.extend(page_data)
        print(f"    Pagina {page}: {len(page_data)} sismos (subtotal: {len(data)})")

        if not click_next_page(driver):
            break
        time.sleep(1.5)

    return data


def go_back_to_search(driver):
    """Hace clic en 'Realizar otra busqueda' para volver al formulario."""
    try:
        link = driver.find_element(By.LINK_TEXT, "Realizar otra busqueda")
        link.click()
        time.sleep(2)
        return True
    except NoSuchElementException:
        pass

    # Fallback: buscar por href parcial
    try:
        link = driver.find_element(
            By.CSS_SELECTOR, "a[href='buscar_sismo']"
        )
        link.click()
        time.sleep(2)
        return True
    except NoSuchElementException:
        pass

    # Ultimo fallback: navegar directamente
    driver.get(SEARCH_URL)
    time.sleep(3)
    return True


def generate_date_ranges(start, end, days_per_range):
    """Genera pares (inicio, fin) de rangos de fechas."""
    ranges = []
    current = start
    while current < end:
        range_end = min(current + timedelta(days=days_per_range - 1), end)
        ranges.append((current, range_end))
        current = range_end + timedelta(days=1)
    return ranges


# -- Script principal --

def main():
    date_ranges = generate_date_ranges(
        FECHA_INICIO_GLOBAL, FECHA_FIN_GLOBAL, DIAS_POR_RANGO
    )

    print("=" * 60)
    print("INPRES Bulk Scraper - Multiples rangos de fechas")
    print(f"Rango total: {FECHA_INICIO_GLOBAL.strftime('%d/%m/%Y')} -> {FECHA_FIN_GLOBAL.strftime('%d/%m/%Y')}")
    print(f"Dividido en {len(date_ranges)} rangos de {DIAS_POR_RANGO} dias")
    print(f"Guardando en: {OUTPUT_FILE}")
    print("=" * 60)

    # Configurar el navegador
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Descomentar para modo sin ventana
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    all_data = []

    try:
        # Navegar al formulario inicial
        print("\nNavegando a la pagina de busqueda...")
        driver.get(SEARCH_URL)
        time.sleep(3)

        for i, (rango_inicio, rango_fin) in enumerate(date_ranges, 1):
            inicio_str = rango_inicio.strftime("%Y-%m-%d")
            fin_str = rango_fin.strftime("%Y-%m-%d")

            print(f"\n--- Rango {i}/{len(date_ranges)}: "
                  f"{rango_inicio.strftime('%d/%m/%Y')} -> {rango_fin.strftime('%d/%m/%Y')} ---")

            # Llenar formulario y buscar
            try:
                fill_form_and_search(driver, inicio_str, fin_str)
            except Exception as e:
                print(f"  ERROR al llenar formulario: {e}")
                # Intentar volver al formulario
                go_back_to_search(driver)
                time.sleep(2)
                try:
                    fill_form_and_search(driver, inicio_str, fin_str)
                except Exception as e2:
                    print(f"  ERROR persistente, saltando rango: {e2}")
                    go_back_to_search(driver)
                    continue

            # Esperar tabla de resultados
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.ID, "tableFiltro"))
                )
                time.sleep(2)
            except TimeoutException:
                print("  No se encontraron resultados o timeout.")
                go_back_to_search(driver)
                continue

            # Scrapear todas las paginas de este rango
            range_data = scrape_all_pages(driver)
            all_data.extend(range_data)
            print(f"  Sismos en este rango: {len(range_data)} | Total acumulado: {len(all_data)}")

            # Guardar progreso parcial en cada rango
            if all_data:
                save_to_csv(all_data)
                print(f"  Progreso guardado ({len(all_data)} sismos)")

            # Volver al formulario para el siguiente rango
            if i < len(date_ranges):
                print("  Volviendo al formulario...")
                go_back_to_search(driver)
                time.sleep(2)

    except Exception as e:
        print(f"\nERROR inesperado: {e}")
    finally:
        driver.quit()

    # Guardar final
    if all_data:
        save_to_csv(all_data)
        print(f"\n{'=' * 60}")
        print(f"SCRAPING COMPLETADO!")
        print(f"Total de sismos scrapeados: {len(all_data)}")
        print(f"Archivo: {OUTPUT_FILE}")
        print(f"{'=' * 60}")
    else:
        print("\nNo se obtuvieron datos.")


def save_to_csv(data):
    """Guarda los datos en el CSV."""
    fieldnames = [
        "fecha", "hora", "latitud", "longitud",
        "profundidad", "magnitud", "provincia", "sentido",
    ]
    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":
    main()
