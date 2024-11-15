import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta

# Configuración de Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Opcional: Ejecuta Chrome en modo sin cabeza (sin abrir una ventana)
# Inicializar el driver (asegúrate de tener el driver del navegador correspondiente)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


try:
    driver.get('https://www.inpres.gob.ar/desktop/')

    # Esperar hasta que la tabla esté presente
    table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "sismos"))
    )

    rows = table.find_elements(By.XPATH, ".//tbody/tr[position() > 1]")

    target_date = (datetime.now() - timedelta(days=1)).date()

    sismos_data = []

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")

        if len(cells) < 8:
            continue  # Saltar filas con menos celdas de las esperadas

        # Extrae y asigna cada valor en el orden adecuado
        fecha = cells[1].find_element(By.TAG_NAME, "font").text

        # Convierte la fecha al formato adecuado para comparación
        try:
            quake_date = datetime.strptime(fecha, "%d/%m/%Y").date()
        except ValueError:
            continue  # Saltar filas con fechas inválidas

        # Detiene el scraping cuando la fecha es anterior a la fecha objetivo
        if quake_date != target_date:
            continue

        # Asigna las columnas a las variables según el orden deseado
        hora = cells[2].find_element(By.TAG_NAME, "font").text + ":00"
        profundidad = cells[3].find_element(By.TAG_NAME, "font").text
        magnitud = cells[4].find_element(By.TAG_NAME, "font").text
        latitud = cells[5].find_element(By.TAG_NAME, "font").text
        longitud = cells[6].find_element(By.TAG_NAME, "font").text
        provincia = cells[7].find_element(By.TAG_NAME, "font").text

        # Detecta el color de la fuente en latitud o longitud para determinar el sentido
        sentido_color = cells[4].find_element(By.TAG_NAME, "font").get_attribute("color")
        sentido = "Si" if sentido_color == "#ff0000" else "No"

        sismo = {
            'fecha': fecha,
            'hora': hora,
            'latitud': latitud,
            'longitud': longitud,
            'profundidad': profundidad,
            'magnitud': magnitud,
            'provincia': provincia,
            'sentido': sentido,
        }
        sismos_data.append(sismo)

finally:
    driver.quit()

# Ruta relativa desde la carpeta 'selenium' a la carpeta 'data'
#carpeta_data = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data'))

# Ruta completa para el archivo CSV
#output_file = os.path.join(carpeta_data, "test.csv")
output_file = os.path.join(os.path.dirname(__file__), '..', '..', '..','data', 'test.csv')

# Concatenar los nuevos datos al principio del archivo CSV
csv_file_path = output_file

# Leer el contenido actual del archivo CSV (si existe)
try:
    with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        existing_data = list(reader)  # Guarda los datos existentes
except FileNotFoundError:
    existing_data = []  # Si el archivo no existe, iniciamos una lista vacía

# Concatenar los nuevos datos al principio de los existentes
all_data = sismos_data + existing_data

# Escribir los datos (nuevos primero, luego los existentes) en el archivo
with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['fecha', 'hora', 'latitud', 'longitud', 'profundidad', 'magnitud', 'provincia', 'sentido'])
    
    # Escribe el encabezado
    writer.writeheader()
    
    # Escribe todos los datos (nuevos primero, luego los existentes)
    writer.writerows(all_data)

print(f"Datos guardados en {csv_file_path}")