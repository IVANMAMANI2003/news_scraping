import re
from datetime import datetime
from urllib.parse import urljoin

import scrapy
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from items import NewsItem


class PachamamaradioSpider(CrawlSpider):
    name = 'pachamamaradio'
    allowed_domains = ['pachamamaradio.org']
    start_urls = ['https://pachamamaradio.org']
    
    # Reglas para seguir enlaces específicos de Pachamama Radio
    rules = (
        Rule(LinkExtractor(
            allow=[
                r'/seccion/',
                r'/noticia/',
                r'/articulo/',
                r'/post/',
                r'/puno/',
                r'/juliaca/',
                r'/azangaro/',
                r'/san-roman/',
                r'/melgar/',
                r'/lampa/',
                r'/huancane/',
                r'/el-collao/',
                r'/carabaya/',
                r'/sandia/',
                r'/putina/',
                r'/moho/',
                r'/yunguyo/',
                r'/chucuito/',
                r'/san-antonio-de-putina/',
            ],
            deny=[
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
                r'\.pdf$',
                r'\.jpg$',
                r'\.jpeg$',
                r'\.png$',
                r'\.gif$',
                r'\.mp4$',
            ]
        ), callback='parse_article', follow=True),
    )
    
    def parse_article(self, response):
        """Extrae datos de un artículo individual"""
        
        # Verificar si es realmente un artículo
        if not self.is_article_page(response):
            return
        
        item = NewsItem()
        
        # Título
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
            '.single-post-title',
            '.post-single-title'
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
        
        # Contenido
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
            '.single-content',
            '.post-single-content',
            '.single-post-content'
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
        item['fuente'] = 'Pachamama Radio'
        
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
        content = response.css('article p::text, .content p::text').getall()
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
            '.single-post-date::text',
            '.post-single-date::text'
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
        url_categories = ['puno', 'juliaca', 'azangaro', 'san-roman', 'melgar', 'lampa', 'huancane', 'el-collao', 'carabaya', 'sandia', 'putina', 'moho', 'yunguyo', 'chucuito', 'san-antonio-de-putina']
        for cat in url_categories:
            if f'/{cat}/' in url.lower():
                return cat.replace('-', ' ').title()
        
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
