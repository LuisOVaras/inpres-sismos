import scrapy
from datetime import datetime
import locale
locale.setlocale(locale.LC_TIME, 'es_ES')


class SismosHistoricosSpider(scrapy.Spider):
    name = "historicos"
    start_urls = ['http://contenidos.inpres.gob.ar/sismologia/historicos']
    
    
    
    def parse(self, response):
        # Seleccionamos las filas de la tabla con los datos
        rows = response.xpath('//table/tr[position()>1]')  # Ignoramos la primera fila de los títulos

        for row in rows:
            # Extraemos los datos de cada columna de la fila
            fecha_lugar = row.xpath('td[2]/strong/text()').get()
            descripcion = row.xpath('td[2]/text()').get()
            latitud = row.xpath('td[3]/text()').get()
            longitud = row.xpath('td[4]/text()').get()

            # Limpiamos los datos si es necesario
            fecha_lugar = fecha_lugar.strip() if fecha_lugar else ''
            descripcion = descripcion.strip() if descripcion else ''
            latitud = latitud.strip() if latitud else ''
            longitud = longitud.strip() if longitud else ''
            
            try:
                # Separador de provincia y fecha
                fecha_texto, provincia = map(str.strip, fecha_lugar.split(','))
                
                # Convertir la fecha a datetime
                fecha_datetime = datetime.strptime(fecha_texto, '%d de %B de %Y')
                fecha_formateada = fecha_datetime.strftime('%d/%m/%Y')  # Formato día/mes/año

                # Creamos un diccionario con los datos extraídos
                yield {
                    'fecha': fecha_formateada,
                    'provincia': provincia,
                    'descripcion': descripcion,
                    'latitud': latitud,
                    'longitud': longitud,
                }
            except ValueError as e:
                self.logger.error(f"Error al procesar la fila: {fecha_lugar}. Detalles: {e}")
                continue
