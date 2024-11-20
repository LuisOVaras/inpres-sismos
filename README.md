# Proyecto de Sismos - INPRES

Este es un proyecto personal de análisis geoespacial que recopila, procesa y visualiza datos de sismos de la página oficial del INPRES (Instituto Nacional de Prevención Sísmica de Argentina). Utiliza web scraping para obtener información actualizada de los eventos sísmicos, la cual es almacenada, analizada y presentada en mapas interactivos. 

El objetivo principal es ofrecer una herramienta accesible para consultar sismos actuales e históricos, permitiendo a los usuarios explorar patrones geográficos y características clave de los sismos mediante visualizaciones interactivas generadas con GeoPandas y otras bibliotecas geoespaciales. Además, la aplicación incluye una funcionalidad automatizada para mantener los datos al día y mejorar la experiencia del análisis.



## Características principales

- **Automatización diaria**: Los datos de sismos se extraen y actualizan automáticamente utilizando Selenium WebDriver.
- **Visualización geográfica**: Mapeo de los sismos utilizando GeoPandas y tecnologías complementarias para enriquecer los mapas.
- **Interfaz amigable**: Una aplicación web creada con Streamlit para que los usuarios puedan explorar los datos de manera interactiva.
- **Base de datos**: Almacenamiento eficiente de los datos, utilizando SQLite como solución rápida y escalable.

## Tecnologías utilizadas

### Principales
- **[Selenium WebDriver](https://www.selenium.dev/documentation/)**: Para la extracción automatizada de datos de una página web compleja.
- **[Streamlit](https://streamlit.io/)**: Para crear una aplicación web interactiva y amigable.
- **[GeoPandas](https://geopandas.org/)**: Para análisis y visualización geoespacial.
- **[Matplotlib](https://matplotlib.org/)**: Para la creación de gráficos personalizados.
- **[Pandas](https://pandas.pydata.org/)**: Para manipulación y análisis de datos tabulares.
- **[Github Actions](https://github.com/features/actions)**: Para automatizar la ejecución diaria del scraper.

### Complementarias
- **[SQLite](https://www.sqlite.org/)**: Base de datos ligera para almacenar y consultar los datos de sismos.
- **[Webdriver Manager](https://github.com/SergeyPirogov/webdriver_manager)**: Para gestionar automáticamente los drivers de Selenium.
- **[Fiona/Shapely/Cartopy](https://github.com/Toblerity/Fiona)** *(Planeadas)*: Para enriquecer las visualizaciones geográficas y manejar geometrías complejas.

### Secundarias
- **[Scrapy](https://scrapy.org/)**: Utilizado solo en una etapa específica del proyecto para recopilar datos históricos.

## Estructura del proyecto

```plaintext
├── data/                       # Archivos CSV con datos de sismos.
├── .github/workflows/          # Configuración de GitHub Actions para la automatización.
├── inpres_sismos/              # Código relacionado con scraping y procesamiento.
│   ├── db/                     # Scripts para crear la base de datos con SQLite
│   ├── selenium/               # Scripts para scraping con Selenium.
│   ├── spiders/                # Spider Scrapy para datos históricos.
├── app.py                      # Aplicación web de Streamlit.
├── requirements.txt            # Dependencias del proyecto.
└── README.md                   # Documentación del proyecto.
