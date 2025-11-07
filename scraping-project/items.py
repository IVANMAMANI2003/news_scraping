# -*- coding: utf-8 -*-
"""
Items para el proyecto de scraping de noticias
Define la estructura de datos que extraen los spiders
"""

import scrapy


class NewsItem(scrapy.Item):
    """Item para almacenar información de noticias"""
    
    # Información básica
    titulo = scrapy.Field()
    fecha = scrapy.Field()
    hora = scrapy.Field()
    resumen = scrapy.Field()
    contenido = scrapy.Field()
    
    # Metadatos
    categoria = scrapy.Field()
    autor = scrapy.Field()
    tags = scrapy.Field()
    keywords = scrapy.Field()
    
    # URLs e imágenes
    url = scrapy.Field()
    dominio = scrapy.Field()
    imagenes = scrapy.Field()
    imagen_principal = scrapy.Field()
    
    # Fuente
    fuente = scrapy.Field()
    
    # Estadísticas
    caracteres_contenido = scrapy.Field()
    palabras_contenido = scrapy.Field()
    cantidad_imagenes = scrapy.Field()
    tiene_imagenes = scrapy.Field()
    
    # Fechas de procesamiento
    fecha_extraccion = scrapy.Field()
    created_at = scrapy.Field()
    
    # Campos adicionales para compatibilidad
    anio = scrapy.Field()
    mes = scrapy.Field()
    dia = scrapy.Field()
    dia_semana = scrapy.Field()
    longitud_titulo = scrapy.Field()
    longitud_resumen = scrapy.Field()
    tipo_contenido = scrapy.Field()

