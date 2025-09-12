#!/usr/bin/env python3
"""
Spider local para Sin Fronteras - Adaptado desde Colab
Extrae noticias y las guarda en CSV/JSON en la carpeta data/sinfronteras
"""

import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


class SinFronterasLocalScraper:
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
        
        # Crear carpeta de datos si no existe
        self.data_folder = "data/sinfronteras"
        os.makedirs(self.data_folder, exist_ok=True)
        
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
            '[datetime]'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                datetime_attr = date_elem.get('datetime') or date_elem.get('content')
                if datetime_attr:
                    try:
                        dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        fecha = dt.strftime('%Y-%m-%d')
                        hora = dt.strftime('%H:%M:%S')
                        break
                    except:
                        pass
                
                # Si no hay datetime, extraer texto
                date_text = self.clean_text(date_elem.get_text())
                if date_text:
                    fecha = self.parse_date_text(date_text)
                    break
        
        return fecha, hora
    
    def parse_date_text(self, date_text):
        """Parsea texto de fecha a formato estándar"""
        if not date_text:
            return datetime.now().strftime('%Y-%m-%d')
        
        # Patrones comunes en español
        months = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }
        
        date_text = date_text.lower()
        for month_name, month_num in months.items():
            if month_name in date_text:
                # Buscar día y año
                numbers = re.findall(r'\d+', date_text)
                if len(numbers) >= 2:
                    day = numbers[0].zfill(2)
                    year = numbers[-1] if len(numbers[-1]) == 4 else f"20{numbers[-1]}"
                    return f"{year}-{month_num}-{day}"
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def extract_article_data(self, article_url):
        """Extrae todos los datos de un artículo específico"""
        try:
            response = self.get_page(article_url)
            if not response:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer título
            title_selectors = [
                'h1.entry-title',
                'h1.post-title', 
                'h1.article-title',
                '.single-title h1',
                'article h1',
                'h1',
                '.title h1',
                '.entry-header h1'
            ]
            title = ""
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
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
                'meta[name="description"]'
            ]
            resumen = ""
            for selector in summary_selectors:
                if selector.startswith('meta'):
                    summary_elem = soup.select_one(selector)
                    if summary_elem:
                        resumen = self.clean_text(summary_elem.get('content', ''))
                        break
                else:
                    summary_elem = soup.select_one(selector)
                    if summary_elem:
                        resumen = self.clean_text(summary_elem.get_text())
                        break
            
            # Extraer contenido principal
            content_selectors = [
                '.entry-content',
                '.post-content',
                '.article-content',
                '.content',
                'article .text',
                '.single-content',
                '.post-body'
            ]
            contenido = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Eliminar elementos no deseados
                    for unwanted in content_elem.find_all(['script', 'style', 'nav', 'aside', 'footer']):
                        unwanted.decompose()
                    contenido = self.clean_text(content_elem.get_text())
                    break
            
            # Extraer categoría
            category_selectors = [
                '.category',
                '.post-category',
                '.entry-category',
                '.cat-links a',
                '[rel="category"]',
                '.breadcrumb a',
                '.post-categories a'
            ]
            categoria = ""
            for selector in category_selectors:
                cat_elems = soup.select(selector)
                if cat_elems:
                    categories = [self.clean_text(cat.get_text()) for cat in cat_elems]
                    categoria = ", ".join(categories)
                    break
            
            # Extraer autor
            author_selectors = [
                '.author',
                '.post-author',
                '.entry-author',
                '[rel="author"]',
                '.byline',
                '.writer',
                '.author-name'
            ]
            autor = ""
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    autor = self.clean_text(author_elem.get_text())
                    break
            
            # Extraer tags
            tag_selectors = [
                '.tags a',
                '.post-tags a',
                '.entry-tags a',
                '[rel="tag"]'
            ]
            tags = []
            for selector in tag_selectors:
                tag_elems = soup.select(selector)
                if tag_elems:
                    tags = [self.clean_text(tag.get_text()) for tag in tag_elems]
                    break
            
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
                'imagenes': ", ".join(images) if images else "",
                'fuente': 'Sin Fronteras'
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
            
            # Selectores comunes para enlaces de artículos
            article_selectors = [
                'article a[href]',
                '.post a[href]',
                '.entry a[href]',
                '.news-item a[href]',
                'h2 a[href]',
                'h3 a[href]',
                '.title a[href]',
                '.headline a[href]',
                '.post-title a[href]',
                '.entry-title a[href]'
            ]
            
            links = set()
            
            # Buscar enlaces con diferentes selectores
            for selector in article_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    href = elem.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        # Filtrar solo URLs que parezcan artículos
                        if self.is_article_url(full_url):
                            links.add(full_url)
            
            # También buscar todos los enlaces internos
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
            '/wp-admin/', '/wp-content/', '/wp-includes/',
            '/feed/', '/rss/', '/sitemap',
            '.jpg', '.png', '.gif', '.pdf', '.css', '.js',
            '/page/', '/category/', '/tag/', '/author/',
            '/search/', '/contact/', '/about/',
            '#', 'javascript:', 'mailto:',
            '/wp-login', '/wp-json', '/xmlrpc'
        ]
        
        for pattern in exclude_patterns:
            if pattern in url.lower():
                return False
        
        return True
    
    def get_pagination_urls(self, soup):
        """Extrae URLs de paginación"""
        pagination_urls = set()
        
        # Selectores comunes para paginación
        pagination_selectors = [
            '.pagination a[href]',
            '.page-numbers a[href]',
            '.pager a[href]',
            '.nav-links a[href]',
            'a[rel="next"]',
            'a[rel="prev"]',
            '.pagination-next a[href]',
            '.pagination-prev a[href]'
        ]
        
        for selector in pagination_selectors:
            elements = soup.select(selector)
            for elem in elements:
                href = elem.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    pagination_urls.add(full_url)
        
        return list(pagination_urls)
    
    def discover_all_pages(self):
        """Descubre TODAS las páginas del sitio web"""
        print("🔍 Descubriendo TODAS las páginas del sitio...")
        
        pages_to_visit = [self.base_url]
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
                
                # Obtener enlaces de artículos de esta página
                article_links = self.get_article_links_from_page(current_page)
                all_article_urls.update(article_links)
                print(f"  📰 Encontrados {len(article_links)} artículos en esta página")
                
                # Obtener TODOS los enlaces de paginación
                pagination_links = self.get_pagination_urls(soup)
                for link in pagination_links:
                    if link not in visited_pages:
                        pages_to_visit.append(link)
                
                # Buscar enlaces internos adicionales
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if (full_url.startswith(self.base_url) and 
                            full_url not in visited_pages and 
                            full_url not in pages_to_visit and
                            not self.is_article_url(full_url)):
                            pages_to_visit.append(full_url)
                
                time.sleep(1)  # Pausa entre requests
                
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
            print(f"✅ Extraído: {article_data['titulo'][:50]}...")
            return article_data
        else:
            print(f"❌ No se pudo extraer: {url}")
            return None
    
    def scrape_news(self, max_workers=5):
        """Extrae TODAS las noticias del sitio web"""
        print("🚀 Iniciando scraping COMPLETO de Sin Fronteras...")
        
        # Descubrir TODAS las páginas y artículos
        all_article_urls = self.discover_all_pages()
        
        if not all_article_urls:
            print("❌ No se encontraron artículos")
            return []
        
        print(f"📊 Total de artículos a procesar: {len(all_article_urls)}")
        
        # Procesar TODOS los artículos con threading
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.scrape_article, url): url for url in all_article_urls}
            
            completed = 0
            for future in as_completed(future_to_url):
                completed += 1
                if completed % 10 == 0:
                    print(f"🔄 Progreso: {completed}/{len(all_article_urls)} artículos procesados")
                
                # Pausa entre requests
                time.sleep(0.5)
        
        print(f"🎉 Scraping completado! {len(self.all_news)} noticias extraídas")
        return self.all_news
    
    def save_to_csv(self, filename=None):
        """Guarda los datos en formato CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_folder}/sinfronteras_{timestamp}.csv"
        
        if self.all_news:
            df = pd.DataFrame(self.all_news)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"✅ Datos guardados en {filename}")
            return filename
        else:
            print("❌ No hay datos para guardar")
            return None
    
    def save_to_json(self, filename=None):
        """Guarda los datos en formato JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_folder}/sinfronteras_{timestamp}.json"
        
        if self.all_news:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_news, f, ensure_ascii=False, indent=2)
            print(f"✅ Datos guardados en {filename}")
            return filename
        else:
            print("❌ No hay datos para guardar")
            return None

# Función principal para ejecutar
def main():
    print("🚀 Iniciando scraping de Sin Fronteras...")
    print("=" * 50)
    
    scraper = SinFronterasLocalScraper()
    
    # Realizar scraping COMPLETO
    news_data = scraper.scrape_news(max_workers=5)
    
    if news_data:
        # Guardar en CSV y JSON
        csv_file = scraper.save_to_csv()
        json_file = scraper.save_to_json()
        
        print(f"\n🎉 ¡Scraping completado exitosamente!")
        print(f"📊 Total de noticias extraídas: {len(news_data)}")
        print(f"📁 Archivos guardados:")
        print(f"   - CSV: {csv_file}")
        print(f"   - JSON: {json_file}")
        
        # Mostrar estadísticas
        print(f"\n📈 Estadísticas:")
        print(f"   - Promedio de caracteres por artículo: {sum(len(n.get('contenido', '')) for n in news_data) // len(news_data)}")
        print(f"   - Promedio de palabras por artículo: {sum(len(n.get('contenido', '').split()) for n in news_data) // len(news_data)}")
        
        # Mostrar categorías encontradas
        categorias = set()
        for news in news_data:
            if news.get('categoria'):
                categorias.add(news['categoria'])
        if categorias:
            print(f"   - Categorías encontradas: {', '.join(list(categorias)[:5])}")
        
        return csv_file, json_file
    else:
        print("❌ No se pudieron extraer noticias")
        return None, None

if __name__ == "__main__":
    main()
