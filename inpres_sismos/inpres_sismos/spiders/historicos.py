import scrapy

class SismosHistoricosSpider(scrapy.Spider):
    name = "sismos_historicos"
    start_urls = ['http://contenidos.inpres.gob.ar/sismologia/historicos']