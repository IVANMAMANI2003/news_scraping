import scrapy


class NewsItem(scrapy.Item):
    titulo = scrapy.Field()
    fecha = scrapy.Field()
    resumen = scrapy.Field()
    contenido = scrapy.Field()
    categoria = scrapy.Field()
    autor = scrapy.Field()
    tags = scrapy.Field()
    url = scrapy.Field()
    fecha_extraccion = scrapy.Field()
    caracteres_contenido = scrapy.Field()
    palabras_contenido = scrapy.Field()
    imagenes = scrapy.Field()
    fuente = scrapy.Field()  # Para saber de qué medio viene
