# Proyecto de Scraping de Sismos - INPRES

Este es un proyecto personal para obtener, mostrar y visualizar datos de sismos de la página oficial del INPRES (Instituto Nacional de Prevención Sísmica de Argentina). El objetivo es crear una aplicación web que permita consultar sismos actuales e históricos, con visualizaciones interactivas de la ubicación de los sismos usando GeoPandas.

## Características

- **Obtención de datos en tiempo real**: Los datos de sismos son obtenidos directamente del sitio web del INPRES mediante un proceso de web scraping utilizando Scrapy.
- **Visualización de sismos**: Los datos de sismos históricos y actuales se muestran en una tabla interactiva en la aplicación.
- **Mapa interactivo**: Los sismos se visualizan en un mapa utilizando GeoPandas, mostrando las ubicaciones exactas de los eventos sísmicos.
- **Actualización automática**: Los datos se actualizan automáticamente una vez al día, garantizando que siempre se muestren los sismos más recientes.
- **Actualización manual**: Los usuarios pueden actualizar los datos manualmente presionando un botón en la interfaz web.

## Tecnologías utilizadas

- **Scrapy**: Para hacer el web scraping de la página INPRES y extraer los datos de los sismos.
- **Streamlit**: Para construir la aplicación web que muestra los datos de manera interactiva.
- **GeoPandas**: Para mostrar las ubicaciones de los sismos en un mapa.
- **Pandas**: Para manejar y mostrar los datos en formato de tabla.
- **Pandas**: Para el procesamiento de los datos y la visualización de los sismos en formato de tabla.
- **Cron Jobs** (o una alternativa en la nube): Para automatizar la ejecución diaria del scraper.

