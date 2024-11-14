import scrapy

class SismosHistoricosSpider(scrapy.Spider):
    name = "historicos"
    start_urls = ['http://contenidos.inpres.gob.ar/sismologia/historicos']
    
    
    
    def parse(self, response):
        # Seleccionamos las filas de la tabla con los datos
        rows = response.xpath('//table/tr[position()>1]')  # Ignoramos la primera fila de los títulos

        for row in rows:
            # Extraemos los datos de cada columna de la fila
            descripcion = row.xpath('td[2]/text()').get()
            latitud = row.xpath('td[3]/text()').get()
            longitud = row.xpath('td[4]/text()').get()

            # Limpiamos los datos si es necesario
            descripcion = descripcion.strip() if descripcion else ''
            latitud = latitud.strip() if latitud else ''
            longitud = longitud.strip() if longitud else ''

            # Creamos un diccionario con los datos extraídos
            yield {
                'descripcion': descripcion,
                'latitud': latitud,
                'longitud': longitud,
            }
    
