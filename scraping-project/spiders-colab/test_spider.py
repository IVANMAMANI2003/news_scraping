import scrapy

from items import NewsItem


class TestSpider(scrapy.Spider):
    name = 'test'
    start_urls = ['https://httpbin.org/html']
    
    def parse(self, response):
        item = NewsItem()
        item['titulo'] = 'Noticia de prueba'
        item['fecha'] = '2025-01-01'
        item['resumen'] = 'Esta es una noticia de prueba'
        item['contenido'] = 'Contenido de prueba para verificar que el sistema funciona'
        item['categoria'] = 'Prueba'
        item['autor'] = 'Sistema'
        item['tags'] = 'prueba, test'
        item['url'] = response.url
        item['imagenes'] = 'Sin imágenes'
        item['fuente'] = 'Test'
        item['caracteres_contenido'] = len('Contenido de prueba')
        item['palabras_contenido'] = 5
        
        yield item
