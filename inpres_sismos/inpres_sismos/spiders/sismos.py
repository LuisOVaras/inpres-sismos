import scrapy

class SismosSpider(scrapy.Spider):
    name = "sismos"
    start_urls = ['http://contenidos.inpres.gob.ar/sismos_consultados.php?pagina=1&totpag=2205&ctd=66144']

    def parse(self, response):
        # Selecciona las filas de la tabla de sismos
        filas = response.xpath('//table//tr')

        for fila in filas:
            # Extrae el texto de cada celda en la fila
            datos_fila = fila.xpath('.//td/text()').getall()
            if datos_fila:  # Ignora las filas vacías o de encabezado
                yield {
                    'id':datos_fila[0],
                    'fecha': datos_fila[1],
                    'hora': datos_fila[2],
                    'latitud': datos_fila[3],
                    'longitud': datos_fila[4],
                    'profundidad': datos_fila[5],
                    'magnitud': datos_fila[6],
                    'intensidad': datos_fila[7],
                    'provincia': datos_fila[8]
                }

        # Avanza a la siguiente página hasta el total (2205)
        pagina_actual = int(response.url.split('=')[1].split('&')[0])
        if pagina_actual < 2205:
            siguiente_pagina = f'http://contenidos.inpres.gob.ar/sismos_consultados.php?pagina={pagina_actual + 1}&totpag=2205&ctd=66144'
            yield scrapy.Request(siguiente_pagina, callback=self.parse)
