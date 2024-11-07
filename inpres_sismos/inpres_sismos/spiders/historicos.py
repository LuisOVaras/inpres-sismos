import scrapy

class SismosHistoricosSpider(scrapy.Spider):
    name = "historicos"
    start_urls = ['http://contenidos.inpres.gob.ar/sismologia/historicos']
    
    
    
    def parse(self, response):
        # Seleccionamos las filas de la tabla con los datos
        rows = response.xpath('//table/tr[position()>1]')  # Ignoramos la primera fila de los títulos

        for row in rows:
            # Extraemos los datos de cada columna de la fila
            description = row.xpath('td[2]/text()').get()
            latitude = row.xpath('td[3]/text()').get()
            longitude = row.xpath('td[4]/text()').get()

            # Limpiamos los datos si es necesario
            description = description.strip() if description else ''
            latitude = latitude.strip() if latitude else ''
            longitude = longitude.strip() if longitude else ''

            # Creamos un diccionario con los datos extraídos
            yield {
                'description': description,
                'latitude': latitude,
                'longitude': longitude,
            }
    
