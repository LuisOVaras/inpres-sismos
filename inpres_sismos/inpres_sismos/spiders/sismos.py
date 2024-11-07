import scrapy

class SismosSpider(scrapy.Spider):
    name = "sismos"
    start_urls = ['http://contenidos.inpres.gob.ar/sismos_consultados.php?pagina=1&totpag=2493&ctd=74773']
