#!/usr/bin/env python3
"""
Script para convertir spiders de Google Colab a spiders de Scrapy
"""

import os
import re
from pathlib import Path


def create_scrapy_spider_template(spider_name, base_url, allowed_domains):
    """Crea un template de spider de Scrapy basado en un spider de Colab"""
    
    template = f'''import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request
from items import NewsItem
import re
from datetime import datetime
from urllib.parse import urljoin

class {spider_name.title()}Spider(CrawlSpider):
    name = '{spider_name}'
    allowed_domains = {allowed_domains}
    start_urls = ['{base_url}']
    
    # Reglas para seguir enlaces - AJUSTAR SEGÚN EL SITIO
    rules = (
        Rule(LinkExtractor(
            allow=[
                # Agregar patrones de URLs de artículos específicos del sitio
                r'/noticia/',
                r'/articulo/',
                r'/nota/',
                r'/post/',
                r'/actualidad/',
                r'/deportes/',
                r'/economia/',
                r'/politica/',
                r'/local/',
                r'/nacional/',
                r'/internacional/',
            ],
            deny=[
                # Patrones a excluir
                r'/categoria',
                r'/category',
                r'/tag/',
                r'/etiqueta/',
                r'/autor/',
                r'/author/',
                r'/buscar',
                r'/search',
                r'/page/',
                r'/pagina/',
                r'#',
                r'\\.pdf$',
                r'\\.jpg$',
                r'\\.jpeg$',
                r'\\.png$',
                r'\\.gif$',
                r'\\.mp4$',
            ]
        ), callback='parse_article', follow=True),
    )
    
    def parse_article(self, response):
        """Extrae datos de un artículo individual"""
        
        # Verificar si es realmente un artículo
        if not self.is_article_page(response):
            return
        
        item = NewsItem()
        
        # Título - AJUSTAR SELECTORES SEGÚN EL SITIO
        title_selectors = [
            'h1.entry-title',
            'h1.post-title',
            'h1.article-title',
            'h1.title',
            '.entry-header h1',
            '.post-header h1',
            '.article-header h1',
            'article h1',
            '.content-title',
            '.main-title',
            'h1',
            '.headline',
        ]
        
        for selector in title_selectors:
            title = response.css(selector + '::text').get()
            if title and title.strip():
                item['titulo'] = title.strip()
                break
        else:
            # Fallback: título de la página
            title = response.css('title::text').get()
            if title:
                # Limpiar título (remover nombre del sitio)
                if ' | ' in title:
                    title = title.split(' | ')[0]
                elif ' - ' in title:
                    title = title.split(' - ')[0]
                item['titulo'] = title.strip()
            else:
                item['titulo'] = "Sin título"
        
        # Fecha
        item['fecha'] = self.extract_date(response)
        
        # Contenido - AJUSTAR SELECTORES SEGÚN EL SITIO
        content_selectors = [
            '.entry-content',
            '.post-content',
            '.article-content',
            '.content',
            '.text-content',
            '.main-content',
            'article .content',
            'article .text',
            '.article-body',
            '.post-body',
            '.entry-body',
            'main article',
            '.single-content'
        ]
        
        content = ""
        for selector in content_selectors:
            content_elements = response.css(selector + ' p::text').getall()
            if content_elements:
                content = ' '.join([elem.strip() for elem in content_elements if elem.strip()])
                if len(content) > 100:
                    break
        
        item['contenido'] = content if content else "Contenido no encontrado"
        
        # Resumen
        item['resumen'] = self.extract_summary(response, content)
        
        # Categoría
        item['categoria'] = self.extract_category(response)
        
        # Autor
        item['autor'] = self.extract_author(response)
        
        # Tags
        item['tags'] = self.extract_tags(response)
        
        # URL
        item['url'] = response.url
        
        # Imágenes
        item['imagenes'] = self.extract_images(response)
        
        # Fuente
        item['fuente'] = '{spider_name.title()}'
        
        # Estadísticas del contenido
        if content:
            item['caracteres_contenido'] = len(content)
            item['palabras_contenido'] = len(content.split())
        else:
            item['caracteres_contenido'] = 0
            item['palabras_contenido'] = 0
        
        yield item
    
    def is_article_page(self, response):
        """Verifica si la página es un artículo"""
        # Verificar que tenga título
        title = response.css('h1::text').get()
        if not title or len(title.strip()) < 10:
            return False
        
        # Verificar que tenga contenido
        content = response.css('article p::text').getall()
        if not content or len(' '.join(content)) < 100:
            return False
        
        return True
    
    def extract_date(self, response):
        """Extrae la fecha del artículo"""
        # Meta tags de fecha
        meta_selectors = [
            'meta[property="article:published_time"]::attr(content)',
            'meta[property="article:modified_time"]::attr(content)',
            'meta[name="publish_date"]::attr(content)',
            'meta[name="date"]::attr(content)',
            'meta[name="pubdate"]::attr(content)',
        ]
        
        for selector in meta_selectors:
            date = response.css(selector).get()
            if date:
                return date
        
        # Selectores de elementos de fecha
        date_selectors = [
            '.entry-date::text',
            '.post-date::text',
            '.article-date::text',
            '.published::text',
            '.date::text',
            '.fecha::text',
            'time::text',
            '.entry-meta .date::text',
            '.post-meta .date::text',
            '.article-meta .date::text',
        ]
        
        for selector in date_selectors:
            date = response.css(selector).get()
            if date and len(date.strip()) > 5:
                return date.strip()
        
        return "Fecha no encontrada"
    
    def extract_summary(self, response, content):
        """Extrae o genera un resumen del artículo"""
        # Meta description
        meta_desc = response.css('meta[name="description"]::attr(content)').get()
        if meta_desc and len(meta_desc.strip()) > 20:
            return meta_desc.strip()
        
        # Open Graph description
        og_desc = response.css('meta[property="og:description"]::attr(content)').get()
        if og_desc and len(og_desc.strip()) > 20:
            return og_desc.strip()
        
        # Extractos específicos
        excerpt_selectors = [
            '.excerpt::text',
            '.summary::text',
            '.lead::text',
            '.intro::text',
            '.article-summary::text',
            '.post-excerpt::text'
        ]
        
        for selector in excerpt_selectors:
            excerpt = response.css(selector).get()
            if excerpt and len(excerpt.strip()) > 20:
                return excerpt.strip()
        
        # Generar resumen del contenido
        if content and len(content) > 200:
            # Tomar las primeras 2-3 oraciones
            sentences = re.split(r'[.!?]+', content)
            summary_sentences = []
            char_count = 0
            
            for sentence in sentences[:4]:
                sentence = sentence.strip()
                if sentence and len(sentence) > 10:
                    if char_count + len(sentence) < 300:
                        summary_sentences.append(sentence)
                        char_count += len(sentence)
                    else:
                        break
            
            if summary_sentences:
                return '. '.join(summary_sentences) + '.'
        
        return "Resumen no disponible"
    
    def extract_category(self, response):
        """Extrae la categoría del artículo"""
        # Buscar en breadcrumbs
        breadcrumb_selectors = [
            '.breadcrumb a:last-child::text',
            '.breadcrumbs a:last-child::text',
            '.breadcrumb li:last-child::text',
            '.breadcrumbs li:last-child::text'
        ]
        
        for selector in breadcrumb_selectors:
            cat = response.css(selector).get()
            if cat and cat.strip().lower() not in ['inicio', 'home', 'principal']:
                return cat.strip()
        
        # Selectores específicos de categoría
        category_selectors = [
            '.category a::text',
            '.categories a::text',
            '.cat-links a::text',
            '.entry-category::text',
            '.post-category::text',
            '.article-category::text',
            '.section::text',
            '.meta-category::text'
        ]
        
        for selector in category_selectors:
            cat = response.css(selector).get()
            if cat and cat.strip():
                return cat.strip()
        
        # Extraer de la URL
        url = response.url
        url_categories = ['actualidad', 'deportes', 'economia', 'politica', 'local', 'nacional', 'internacional']
        for cat in url_categories:
            if f'/{cat}/' in url.lower():
                return cat.title()
        
        return "Sin categoría"
    
    def extract_author(self, response):
        """Extrae el autor del artículo"""
        # Meta tags
        meta_author = response.css('meta[name="author"]::attr(content)').get()
        if meta_author:
            return meta_author.strip()
        
        # Selectores de autor
        author_selectors = [
            '.author a::text',
            '.by-author::text',
            '.entry-author::text',
            '.post-author::text',
            '.article-author::text',
            '.author-name::text',
            '.byline::text',
            '.meta-author::text',
            '.writer::text'
        ]
        
        for selector in author_selectors:
            author = response.css(selector).get()
            if author and len(author.strip()) < 100:
                # Limpiar prefijos comunes
                author = re.sub(r'^(por|by|autor|escrito por)[:|\s]+', '', author.strip(), flags=re.IGNORECASE)
                if author:
                    return author
        
        return "Autor no especificado"
    
    def extract_tags(self, response):
        """Extrae los tags del artículo"""
        tag_selectors = [
            '.tags a::text',
            '.tag-links a::text',
            '.entry-tags a::text',
            '.post-tags a::text',
            '.article-tags a::text',
            '.hashtags a::text',
            '.keywords a::text'
        ]
        
        tags = []
        for selector in tag_selectors:
            tag_elements = response.css(selector).getall()
            for tag in tag_elements:
                tag = tag.strip()
                if tag and tag not in tags:
                    tags.append(tag)
        
        # Buscar en meta keywords
        meta_keywords = response.css('meta[name="keywords"]::attr(content)').get()
        if meta_keywords:
            keywords = meta_keywords.split(',')
            tags.extend([k.strip() for k in keywords if k.strip()])
        
        return ', '.join(tags[:10]) if tags else "Sin tags"
    
    def extract_images(self, response):
        """Extrae información de imágenes del artículo"""
        images = []
        
        # Buscar imágenes en el contenido principal
        img_elements = response.css('article img[src], .content img[src], .entry-content img[src]')
        
        for img in img_elements:
            src = img.css('::attr(src)').get()
            if src:
                # Convertir a URL absoluta
                full_url = urljoin(response.url, src)
                
                # Filtrar imágenes muy pequeñas o de interface
                width = img.css('::attr(width)').get()
                height = img.css('::attr(height)').get()
                
                if width and height:
                    try:
                        w, h = int(width), int(height)
                        if w < 100 or h < 100:  # Muy pequeñas, probablemente iconos
                            continue
                    except ValueError:
                        pass
                
                # Filtrar por nombre de archivo
                if any(skip in src.lower() for skip in ['icon', 'logo', 'avatar', 'button', 'banner']):
                    continue
                
                alt = img.css('::attr(alt)').get() or ''
                title = img.css('::attr(title)').get() or ''
                
                images.append({
                    'url': full_url,
                    'alt': alt.strip(),
                    'title': title.strip()
                })
        
        return str(images) if images else "Sin imágenes"
'''
    
    return template

def main():
    """Función principal"""
    print("🔄 Convertidor de Spiders de Colab a Scrapy")
    print("=" * 50)
    
    # Configuraciones de los spiders
    spiders_config = [
        {
            'name': 'pachamamaradio',
            'base_url': 'https://pachamamaradio.org',
            'allowed_domains': ["pachamamaradio.org"]
        },
        {
            'name': 'punonoticias',
            'base_url': 'https://punonoticias.com',
            'allowed_domains': ["punonoticias.com"]
        },
        {
            'name': 'sinfronteras',
            'base_url': 'https://sinfronteras.com.pe',
            'allowed_domains': ["sinfronteras.com.pe"]
        }
    ]
    
    for config in spiders_config:
        print(f"📝 Creando spider: {config['name']}")
        
        template = create_scrapy_spider_template(
            config['name'],
            config['base_url'],
            config['allowed_domains']
        )
        
        filename = f"spiders/{config['name']}_scrapy_spider.py"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print(f"✅ Spider creado: {filename}")
    
    print("\n" + "=" * 50)
    print("🎉 ¡Conversión completada!")
    print("\n📝 Próximos pasos:")
    print("1. Revisa cada spider creado")
    print("2. Ajusta los selectores CSS según cada sitio")
    print("3. Modifica las reglas de enlaces (allow/deny)")
    print("4. Prueba cada spider individualmente")
    print("5. Ejecuta: python test_scraping.py")

if __name__ == "__main__":
    main()
