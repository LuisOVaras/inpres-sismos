import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException


# Configuración de Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Opcional: Ejecuta Chrome en modo sin cabeza (sin abrir una ventana)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# URL base
base_url = "https://www.inpres.gob.ar/desktop/"

# Ruta relativa desde la carpeta 'selenium' a la carpeta 'data'
carpeta_data = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data'))

# Ruta completa para el archivo CSV
output_file = os.path.join(carpeta_data, "sismos.csv")


# Configura el archivo CSV para guardar los datos
#output_file = "sismos.csv"
with open(output_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["fecha", "hora", "latitud", "longitud", "profundidad", "magnitud", "provincia", "sentido"])
    
    # Hacer clic en los botones antes de comenzar el scraping
    driver.get(base_url)  # Carga la primera página

    # Ejemplo de clic en dos botones (ajusta los selectores según corresponda)
    boton1 = driver.find_element(By.XPATH, '/html/body/div/section/div/div[3]/table[1]/tbody/tr[13]/td/a')
    boton1.click()
    time.sleep(2)  # Espera para que el clic se procese

    # Ingresar fechas en los dos inputs
    fecha_inicio = driver.find_element(By.XPATH, '//*[@id="datepicker"]')  # Reemplaza con el ID del primer input
    fecha_inicio.click()
    # Encuentra el elemento select
    select_year = driver.find_element(By.XPATH, '//*[@id="ui-datepicker-div"]/div/div/select[2]')
    select_year.click()

    # Usa JavaScript para agregar la opción 1998 al <select>
    driver.execute_script("let option = document.createElement('option');"
                        "option.value = '1998';"
                        "option.text = '1998';"
                        "arguments[0].appendChild(option);", select_year)

    # Selecciona la opción recién creada con value '1998'
    select = Select(select_year)
    select.select_by_value("1998")
    time.sleep(1)
    
    dia = driver.find_element(By.XPATH, '//*[@id="ui-datepicker-div"]/table/tbody/tr[1]/td[7]')
    dia.click()
    time.sleep(1)

    fecha_fin = driver.find_element(By.ID, 'datepicker2')  # Reemplaza con el ID del segundo input
    fecha_fin.click()

    select_year = driver.find_element(By.XPATH, '//*[@id="ui-datepicker-div"]/div/div/select[2]')
    select_year.click()

    select = Select(select_year)
    select.select_by_value("2024")
    time.sleep(1)
    
    dia = driver.find_element(By.XPATH, '//*[@id="ui-datepicker-div"]/table/tbody/tr[2]/td[6]')
    dia.click()
    time.sleep(1)

    # Seleccionar el checkbox
    checkbox = driver.find_element(By.ID, 'tilde1')  # Reemplaza con el ID del checkbox
    checkbox.click()  # Hacer clic en el checkbox para seleccionarlo
    time.sleep(1)  # Pausa para asegurar que se selecciona el checkbox

    boton2 = driver.find_element(By.ID, 'boton')
    boton2.click()
    time.sleep(2)
    
    # Número de páginas a recorrer
    max_paginas = 2
    pagina_actual = 0  # Contador para las páginas


    # Bucle para recorrer las páginas de manera indefinida hasta que no haya botón de "Siguiente"
    while pagina_actual < max_paginas:
        # Espera para asegurar que la página esté cargada
        time.sleep(5)
        
        # Selecciona las filas de datos
        filas = driver.find_elements(By.XPATH, '//*[@id="sismos"]/tbody/tr[position() > 3]')
        
        # Verifica si se encontraron filas
        if not filas:
            print("No se encontraron filas en esta página.")
            break  # Rompe el bucle si no se encuentran filas

        # Extrae los datos de cada fila
        for fila in filas:
            try:
                fecha = fila.find_element(By.XPATH, './/td[2]').text
                hora = fila.find_element(By.XPATH, './/td[3]').text
                latitud = fila.find_element(By.XPATH, './/td[4]').text
                longitud = fila.find_element(By.XPATH, './/td[5]').text
                profundidad = fila.find_element(By.XPATH, './/td[6]').text
                magnitud = fila.find_element(By.XPATH, './/td[7]').text
                intensidad = fila.find_element(By.XPATH, './/td[8]').text
                provincia = fila.find_element(By.XPATH, './/td[9]').text
                
                # Determina si es "sentido" basado en el color del texto en magnitud
                sentido = "No"
                try:
                    # Intentar encontrar el elemento <font> dentro de <td[7]>
                    magnitud_element = fila.find_element(By.XPATH, './/td[7]/div/font')
                    font_color = magnitud_element.get_attribute("color")
                    if font_color == "#FF0000":  # Verifica si el color es rojo
                        sentido = "Si"
                except NoSuchElementException:
                    pass
                
                # Guarda los datos en el CSV
                writer.writerow([fecha, hora, latitud, longitud, profundidad, magnitud, provincia, sentido])

            except Exception as e:
                print(f"Error al procesar una fila: {e}")
        
        # Incrementa el contador de páginas
        print(f"Scraping página {pagina_actual}...")
        pagina_actual += 1
        
        # Intenta hacer clic en el botón de "Siguiente" para ir a la próxima página
        try:
            boton_siguiente = driver.find_element(By.XPATH, '//tbody/tr/td/font/a[contains(text(),"Siguiente ")]')  # Ajusta el XPATH según corresponda
            boton_siguiente.click()
        except NoSuchElementException:
            print("No se encontró el botón de 'Siguiente'. Fin del scraping.")
            break  # Si no hay botón de "Siguiente", sal del bucle

# Cerrar el navegador
driver.quit()
print(f"Datos guardados en {output_file}")
