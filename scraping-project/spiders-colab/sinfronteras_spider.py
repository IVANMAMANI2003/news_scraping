import csv
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


class DiarioSinFronterasScraper:
    def __init__(self):
        self.base_url = "https://diariosinfronteras.com.pe"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache'
        })
        self.all_news = []
        self.processed_urls = set()
        self.lock = threading.Lock()
        
    def get_page(self, url, retries=3):
        """Obtiene el contenido de una página con reintentos"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except Exception as e:
                print(f"Error en intento {attempt + 1} para {url}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(3)
                else:
                    return None
    
    def extract_images(self, soup):
        """Extrae todas las imágenes de un artículo"""
        images = []
        img_selectors = [
            'img[src]',
            'img[data-src]',
            'img[data-lazy-src]',
            '.wp-post-image',
            '.featured-image img',
            '.post-thumbnail img',
            '.entry-content img',
            '.article-content img'
        ]
        
        for selector in img_selectors:
            img_tags = soup.select(selector)
            for img in img_tags:
                src = (img.get('src') or 
                      img.get('data-src') or 
                      img.get('data-lazy-src') or 
                      img.get('data-original'))
                if src and src not in [img.split('?')[0] for img in images]:
                    full_url = urljoin(self.base_url, src)
                    if self.is_valid_image_url(full_url):
                        images.append(full_url)
        return images
    
    def is_valid_image_url(self, url):
        """Verifica si la URL es una imagen válida"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        return any(ext in url.lower() for ext in image_extensions)
    
    def clean_text(self, text):
        """Limpia y normaliza el texto"""
        if not text:
            return ""
        # Eliminar espacios extra y caracteres especiales
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[\r\n\t]', ' ', text)
        text = re.sub(r'[^\w\s\-.,;:!?()áéíóúüñÁÉÍÓÚÜÑ]', ' ', text)
        return text.strip()
    
    def extract_date_time(self, soup):
        """Extrae fecha y hora del artículo"""
        fecha = ""
        hora = ""
        
        # Múltiples selectores para fecha
        date_selectors = [
            'time[datetime]',
            '.entry-date',
            '.post-date',
            '.published',
            '.date',
            '.post-meta time',
            '.entry-meta time',
            'meta[property="article:published_time"]',
            'meta[name="article:published_time"]',
            '.post-published-date'
        ]
        
        for selector in date_selectors:
            if selector.startswith('meta'):
                date_elem = soup.select_one(selector)
                if date_elem:
                    content = date_elem.get('content')
                    if content:
                        try:
                            dt = datetime.fromisoformat(content.replace('Z', '+00:00'))
                            fecha = dt.strftime('%Y-%m-%d')
                            hora = dt.strftime('%H:%M:%S')
                            return fecha, hora
                        except:
                            continue
            else:
                date_elem = soup.select_one(selector)
                if date_elem:
                    datetime_attr = date_elem.get('datetime')
                    if datetime_attr:
                        try:
                            dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                            fecha = dt.strftime('%Y-%m-%d')
                            hora = dt.strftime('%H:%M:%S')
                            return fecha, hora
                        except:
                            pass
                    
                    # Extraer texto de fecha
                    date_text = self.clean_text(date_elem.get_text())
                    if date_text and len(date_text) > 5:
                        fecha = date_text
                        return fecha, hora
        
        return fecha, hora
    
    def extract_article_data(self, article_url):
        """Extrae todos los datos de un artículo específico"""
        try:
            response = self.get_page(article_url)
            if not response:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer título con múltiples selectores
            title_selectors = [
                'h1.entry-title',
                'h1.post-title',
                'h1.article-title',
                '.post-header h1',
                '.entry-header h1',
                'article h1',
                '.single-post h1',
                'h1',
                'title'
            ]
            
            title = ""
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    if title and len(title) > 5:
                        break
            
            # Extraer fecha y hora
            fecha, hora = self.extract_date_time(soup)
            
            # Extraer resumen/excerpt
            summary_selectors = [
                '.entry-excerpt',
                '.post-excerpt',
                '.excerpt',
                '.lead',
                '.summary',
                '.post-summary',
                'meta[name="description"]',
                'meta[property="og:description"]',
                '.entry-content p:first-of-type'
            ]
            
            resumen = ""
            for selector in summary_selectors:
                if selector.startswith('meta'):
                    summary_elem = soup.select_one(selector)
                    if summary_elem:
                        content = summary_elem.get('content')
                        if content:
                            resumen = self.clean_text(content)
                            break
                else:
                    summary_elem = soup.select_one(selector)
                    if summary_elem:
                        text = self.clean_text(summary_elem.get_text())
                        if text and len(text) > 20:
                            resumen = text[:300] + "..." if len(text) > 300 else text
                            break
            
            # Extraer contenido principal
            content_selectors = [
                '.entry-content',
                '.post-content',
                '.article-content',
                '.content',
                'article .text',
                '.post-body',
                '.single-content',
                '.post-text',
                'article'
            ]
            
            contenido = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Eliminar elementos no deseados
                    for unwanted in content_elem.find_all(['script', 'style', 'nav', 'aside', 'footer', 'header', '.ads', '.advertisement']):
                        unwanted.decompose()
                    
                    text = self.clean_text(content_elem.get_text())
                    if text and len(text) > 50:
                        contenido = text
                        break
            
            # Extraer categoría
            category_selectors = [
                '.category a',
                '.post-category a',
                '.entry-category a',
                '.cat-links a',
                '[rel="category tag"]',
                '.breadcrumb a',
                '.post-categories a',
                '.entry-meta .category'
            ]
            
            categorias = []
            for selector in category_selectors:
                cat_elems = soup.select(selector)
                for cat_elem in cat_elems:
                    cat_text = self.clean_text(cat_elem.get_text())
                    if cat_text and cat_text not in categorias:
                        categorias.append(cat_text)
            
            categoria = ", ".join(categorias) if categorias else ""
            
            # Extraer autor
            author_selectors = [
                '.author a',
                '.post-author a',
                '.entry-author a',
                '[rel="author"]',
                '.byline a',
                '.writer a',
                '.author-name',
                '.post-meta .author',
                '.entry-meta .author'
            ]
            
            autor = ""
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    autor = self.clean_text(author_elem.get_text())
                    if autor and len(autor) > 2:
                        break
            
            # Extraer tags
            tag_selectors = [
                '.tags a',
                '.post-tags a',
                '.entry-tags a',
                '[rel="tag"]',
                '.tag-links a',
                '.post-meta .tags a'
            ]
            
            tags = []
            for selector in tag_selectors:
                tag_elems = soup.select(selector)
                for tag_elem in tag_elems:
                    tag_text = self.clean_text(tag_elem.get_text())
                    if tag_text and tag_text not in tags:
                        tags.append(tag_text)
            
            # Extraer imágenes
            images = self.extract_images(soup)
            
            return {
                'titulo': title,
                'fecha': fecha,
                'hora': hora,
                'resumen': resumen,
                'contenido': contenido,
                'categoria': categoria,
                'autor': autor,
                'tags': ", ".join(tags) if tags else "",
                'url': article_url,
                'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'link_imagenes': ", ".join(images) if images else ""
            }
            
        except Exception as e:
            print(f"Error extrayendo artículo {article_url}: {str(e)}")
            return None
    
    def get_article_links_from_page(self, page_url):
        """Extrae todos los enlaces de artículos de una página"""
        try:
            response = self.get_page(page_url)
            if not response:
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Selectores específicos para enlaces de artículos
            article_selectors = [
                'article a[href]',
                '.post a[href]',
                '.entry a[href]',
                '.news-item a[href]',
                '.post-title a[href]',
                '.entry-title a[href]',
                'h1 a[href]',
                'h2 a[href]',
                'h3 a[href]',
                '.title a[href]',
                '.headline a[href]',
                '.post-header a[href]',
                '.entry-header a[href]',
                '.content-area a[href]'
            ]
            
            links = set()
            
            # Buscar enlaces con selectores específicos
            for selector in article_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    href = elem.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if self.is_article_url(full_url):
                            links.add(full_url)
            
            # Buscar todos los enlaces internos como respaldo
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if self.is_article_url(full_url):
                        links.add(full_url)
            
            return list(links)
            
        except Exception as e:
            print(f"Error obteniendo enlaces de {page_url}: {str(e)}")
            return []
    
    def is_article_url(self, url):
        """Determina si una URL es probablemente un artículo"""
        if not url.startswith(self.base_url):
            return False
            
        # Excluir URLs que no son artículos
        exclude_patterns = [
            '/wp-admin/', '/wp-content/', '/wp-includes/', '/wp-json/',
            '/feed/', '/rss/', '/sitemap', '/robots.txt',
            '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.css', '.js', '.ico',
            '/page/', '/paged/', '/category/', '/tag/', '/author/', '/archivo/',
            '/search/', '/contact/', '/about/', '/privacy/', '/terms/',
            '/login/', '/register/', '/admin/',
            '#', 'javascript:', 'mailto:', 'tel:',
            '?replytocom=', '?share=', '?print=',
            '/comentarios/', '/comment/'
        ]
        
        url_lower = url.lower()
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False
        
        # URLs que probablemente son artículos
        article_indicators = [
            '/noticia/', '/nota/', '/articulo/', '/post/', '/story/',
            datetime.now().strftime('%Y'),
            str(datetime.now().year - 1),
            '/noticias/', '/actualidad/', '/deportes/', '/politica/',
            '/economia/', '/cultura/', '/sociedad/'
        ]
        
        # Si contiene indicadores de artículo, es más probable que sea uno
        for indicator in article_indicators:
            if indicator in url_lower:
                return True
        
        # Si tiene estructura de fecha (YYYY/MM/DD) o slug largo
        if (re.search(r'/\d{4}/\d{2}/', url) or 
            re.search(r'/[a-zA-Z0-9\-]{10,}/?$', url)):
            return True
        
        return len(url.split('/')) >= 4  # URLs con al menos cierta profundidad
    
    def get_pagination_urls(self, soup):
        """Extrae URLs de paginación"""
        pagination_urls = set()
        
        # Selectores para paginación
        pagination_selectors = [
            '.pagination a[href]',
            '.page-numbers a[href]',
            '.pager a[href]',
            '.nav-links a[href]',
            '.page-nav a[href]',
            '.wp-pagenavi a[href]',
            'a[rel="next"]',
            'a[rel="prev"]',
            '.next-page[href]',
            '.prev-page[href]'
        ]
        
        for selector in pagination_selectors:
            elements = soup.select(selector)
            for elem in elements:
                href = elem.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if full_url.startswith(self.base_url):
                        pagination_urls.add(full_url)
        
        return list(pagination_urls)
    
    def discover_all_pages(self):
        """Descubre todas las páginas del sitio web"""
        print("🔍 Descubriendo todas las páginas del sitio...")
        
        pages_to_visit = [
            self.base_url,
            f"{self.base_url}/noticias/",
            f"{self.base_url}/actualidad/",
            f"{self.base_url}/deportes/",
            f"{self.base_url}/politica/",
            f"{self.base_url}/economia/",
            f"{self.base_url}/cultura/",
            f"{self.base_url}/sociedad/"
        ]
        
        visited_pages = set()
        all_article_urls = set()
        
        while pages_to_visit:
            current_page = pages_to_visit.pop(0)
            
            if current_page in visited_pages:
                continue
                
            print(f"📄 Explorando: {current_page}")
            visited_pages.add(current_page)
            
            try:
                response = self.get_page(current_page)
                if not response:
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Obtener enlaces de artículos
                article_links = self.get_article_links_from_page(current_page)
                new_articles = set(article_links) - all_article_urls
                all_article_urls.update(new_articles)
                
                if new_articles:
                    print(f"  📰 Encontrados {len(new_articles)} nuevos artículos")
                
                # Obtener enlaces de paginación
                pagination_links = self.get_pagination_urls(soup)
                for link in pagination_links:
                    if link not in visited_pages and link not in pages_to_visit:
                        pages_to_visit.append(link)
                
                # Buscar enlaces de categorías y secciones
                category_selectors = [
                    'nav a[href]',
                    '.menu a[href]',
                    '.category a[href]',
                    '.categories a[href]'
                ]
                
                for selector in category_selectors:
                    elements = soup.select(selector)
                    for elem in elements:
                        href = elem.get('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            if (full_url.startswith(self.base_url) and 
                                full_url not in visited_pages and 
                                full_url not in pages_to_visit and
                                not self.is_article_url(full_url)):
                                pages_to_visit.append(full_url)
                
                time.sleep(2)  # Pausa respetuosa entre requests
                
            except Exception as e:
                print(f"Error explorando {current_page}: {str(e)}")
                continue
        
        print(f"✅ Descubrimiento completado. {len(all_article_urls)} artículos encontrados")
        return list(all_article_urls)
    
    def scrape_article(self, url):
        """Scraper individual para un artículo con thread safety"""
        with self.lock:
            if url in self.processed_urls:
                return None
            self.processed_urls.add(url)
        
        print(f"📖 Extrayendo: {url}")
        article_data = self.extract_article_data(url)
        
        if article_data and article_data['titulo']:
            with self.lock:
                self.all_news.append(article_data)
            print(f"✅ Extraído: {article_data['titulo'][:60]}...")
            return article_data
        else:
            print(f"❌ No se pudo extraer: {url}")
            return None
    
    def scrape_all_news(self, max_workers=3):
        """Extrae todas las noticias del sitio web"""
        print("🚀 Iniciando scraping completo de Diario Sin Fronteras...")
        
        # Descubrir todas las páginas y artículos
        all_article_urls = self.discover_all_pages()
        
        if not all_article_urls:
            print("❌ No se encontraron artículos")
            return
        
        print(f"📊 Total de artículos a procesar: {len(all_article_urls)}")
        
        # Procesar artículos con threading
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.scrape_article, url): url for url in all_article_urls}
            
            completed = 0
            for future in as_completed(future_to_url):
                completed += 1
                if completed % 5 == 0:
                    print(f"🔄 Progreso: {completed}/{len(all_article_urls)} artículos procesados")
                
                # Pausa entre requests
                time.sleep(1)
        
        print(f"🎉 Scraping completado! {len(self.all_news)} noticias extraídas")
    
    def save_to_csv(self, filename='diariosinfronteras_noticias.csv'):
        """Guarda los datos en formato CSV"""
        if not self.all_news:
            print("❌ No hay datos para guardar")
            return
        
        df = pd.DataFrame(self.all_news)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 Datos guardados en {filename}")
    
    def save_to_json(self, filename='diariosinfronteras_noticias.json'):
        """Guarda los datos en formato JSON"""
        if not self.all_news:
            print("❌ No hay datos para guardar")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_news, f, ensure_ascii=False, indent=2)
        print(f"💾 Datos guardados en {filename}")

# Función principal para ejecutar el scraper
def main():
    scraper = DiarioSinFronterasScraper()
    
    # Ejecutar el scraping completo
    scraper.scrape_all_news(max_workers=2)  # Conservador para ser respetuoso
    
    # Guardar los resultados
    scraper.save_to_csv('diariosinfronteras_noticias_completas.csv')
    scraper.save_to_json('diariosinfronteras_noticias_completas.json')
    
    print(f"🎯 SCRAPING COMPLETADO")
    print(f"📊 Total de noticias extraídas: {len(scraper.all_news)}")
    print(f"📁 Archivos generados:")
    print(f"  - diariosinfronteras_noticias_completas.csv")
    print(f"  - diariosinfronteras_noticias_completas.json")

# Ejecutar el scraper
if __name__ == "__main__":
    main()