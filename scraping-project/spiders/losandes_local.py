#!/usr/bin/env python3
"""
Spider local para Los Andes - Adaptado desde Colab
Extrae noticias y las guarda en CSV/JSON en la carpeta data/losandes
"""

import csv
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


class LosAndesLocalScraper:
    def __init__(self):
        self.base_url = "https://losandes.com.pe"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.all_news = []
        self.processed_urls = set()
        self.lock = threading.Lock()
        self.max_pages_to_explore = 1000
        
        # Crear carpeta de datos si no existe
        self.data_folder = "data/losandes"
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
                    time.sleep(2)
                else:
                    return None
    
    def extract_images(self, soup):
        """Extrae imágenes de un artículo (máximo 2)
        Busca en etiquetas img y también en estilos CSS (background-image)
        """
        images = []
        
        # 1. Buscar en etiquetas <img>
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                # Filtrar imágenes muy pequeñas o de interface
                width = img.get('width')
                height = img.get('height')
                
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
                
                full_url = urljoin(self.base_url, src)
                if full_url not in images:
                    images.append(full_url)
                    
                    # Limitar a máximo 2 imágenes
                    if len(images) >= 2:
                        return images
        
        # 2. Buscar en atributos style con background-image
        # Buscar elementos con atributo style que contenga background-image
        all_elements = soup.find_all(True)  # Todos los elementos
        
        for elem in all_elements:
            style_attr = elem.get('style', '')
            if style_attr and ('background-image' in style_attr or 'background:' in style_attr):
                # Extraer URL de background-image usando regex
                # Patrón: background-image: url(...) o background: url(...)
                bg_patterns = [
                    r'background-image:\s*url\(["\']?([^"\')]+)["\']?\)',
                    r'background:\s*url\(["\']?([^"\')]+)["\']?\)',
                    r'background-image:\s*url\(([^)]+)\)',
                    r'background:\s*url\(([^)]+)\)'
                ]
                
                for pattern in bg_patterns:
                    matches = re.findall(pattern, style_attr, re.IGNORECASE)
                    for match in matches:
                        # Limpiar la URL de comillas y espacios
                        url = match.strip().strip('"\'').strip()
                        if url and url.startswith('http'):
                            if url not in images:
                                images.append(url)
                                if len(images) >= 2:
                                    return images
                        elif url and not url.startswith('data:'):
                            # URL relativa, convertir a absoluta
                            full_url = urljoin(self.base_url, url)
                            if full_url not in images:
                                # Filtrar por nombre de archivo
                                if not any(skip in full_url.lower() for skip in ['icon', 'logo', 'avatar', 'button', 'banner']):
                                    images.append(full_url)
                                    if len(images) >= 2:
                                        return images
        
        # 3. Buscar dentro de etiquetas <style> que contienen CSS
        # Esto es importante porque muchas imágenes están definidas en CSS dentro de <style>
        style_tags = soup.find_all('style')
        
        for style_tag in style_tags:
            style_content = style_tag.string or ''
            if style_content and ('background' in style_content.lower() or 'url(' in style_content.lower()):
                # Buscar URLs en el contenido CSS
                # Patrones para encontrar background: url(...) o background-image: url(...)
                bg_patterns = [
                    r'background-image:\s*url\(["\']?([^"\')]+)["\']?\)',
                    r'background:\s*url\(["\']?([^"\')]+)["\']?\)',
                    r'background-image:\s*url\(([^)]+)\)',
                    r'background:\s*url\(([^)]+)\)',
                    # Patrón más específico para .tdb-featured-image-bg o .tdi_85
                    r'\.(?:tdb-featured-image-bg|tdi_\d+)[^{]*\{[^}]*background:\s*url\(["\']?([^"\')]+)["\']?\)',
                    r'\.(?:tdb-featured-image-bg|tdi_\d+)[^{]*\{[^}]*background-image:\s*url\(["\']?([^"\')]+)["\']?\)',
                ]
                
                for pattern in bg_patterns:
                    matches = re.findall(pattern, style_content, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        # Limpiar la URL de comillas y espacios
                        url = match.strip().strip('"\'').strip()
                        if url and url.startswith('http'):
                            if url not in images:
                                # Filtrar por nombre de archivo
                                if not any(skip in url.lower() for skip in ['icon', 'logo', 'avatar', 'button', 'banner', 'gradient']):
                                    images.append(url)
                                    if len(images) >= 2:
                                        return images
                        elif url and not url.startswith('data:') and not url.startswith('linear-gradient'):
                            # URL relativa, convertir a absoluta
                            full_url = urljoin(self.base_url, url)
                            if full_url not in images:
                                # Filtrar por nombre de archivo
                                if not any(skip in full_url.lower() for skip in ['icon', 'logo', 'avatar', 'button', 'banner']):
                                    images.append(full_url)
                                    if len(images) >= 2:
                                        return images
        
        # 4. Buscar en elementos con clases específicas de imágenes destacadas
        # Buscar elementos con clases como .tdb-featured-image-bg, .tdi_85, etc.
        featured_selectors = [
            '.tdb-featured-image-bg',
            '.tdi_85',
            '.featured-image',
            '.post-thumbnail',
            '.article-image',
            '[class*="featured"]',
            '[class*="image-bg"]'
        ]
        
        for selector in featured_selectors:
            featured_elems = soup.select(selector)
            for elem in featured_elems:
                # Buscar en el atributo style
                style_attr = elem.get('style', '')
                if style_attr:
                    bg_patterns = [
                        r'background-image:\s*url\(["\']?([^"\')]+)["\']?\)',
                        r'background:\s*url\(["\']?([^"\')]+)["\']?\)',
                    ]
                    for pattern in bg_patterns:
                        matches = re.findall(pattern, style_attr, re.IGNORECASE)
                        for match in matches:
                            url = match.strip().strip('"\'').strip()
                            if url and url.startswith('http'):
                                if url not in images:
                                    images.append(url)
                                    if len(images) >= 2:
                                        return images
                            elif url and not url.startswith('data:'):
                                full_url = urljoin(self.base_url, url)
                                if full_url not in images:
                                    if not any(skip in full_url.lower() for skip in ['icon', 'logo', 'avatar', 'button', 'banner']):
                                        images.append(full_url)
                                        if len(images) >= 2:
                                            return images
                
                # También buscar imágenes dentro de estos elementos
                img_in_elem = elem.find('img')
                if img_in_elem:
                    src = img_in_elem.get('src') or img_in_elem.get('data-src') or img_in_elem.get('data-lazy-src')
                    if src:
                        full_url = urljoin(self.base_url, src)
                        if full_url not in images:
                            if not any(skip in full_url.lower() for skip in ['icon', 'logo', 'avatar', 'button', 'banner']):
                                images.append(full_url)
                                if len(images) >= 2:
                                    return images
        
        return images
    
    def clean_text(self, text):
        """Limpia y normaliza el texto"""
        if not text:
            return ""
        # Eliminar espacios extra y caracteres especiales
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[\r\n\t]', ' ', text)
        return text
    
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
                '.post-header h1',
                'article h1',
                'h1'
            ]
            title = ""
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    break
            
            # Extraer fecha y hora
            date_selectors = [
                'time',
                '.post-date',
                '.entry-date',
                '.published',
                '.date',
                '[datetime]'
            ]
            fecha = ""
            hora = ""
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
                        fecha = date_text
                        break
            
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
                '.breadcrumb a'
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
                '.writer'
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
                'fuente': 'Los Andes',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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
                '.headline a[href]'
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
            '#', 'javascript:', 'mailto:'
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
            'a[rel="prev"]'
        ]
        
        for selector in pagination_selectors:
            elements = soup.select(selector)
            for elem in elements:
                href = elem.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    pagination_urls.add(full_url)
        
        return list(pagination_urls)
    
    def discover_pages(self):
        """Descubre TODAS las páginas del sitio web"""
        print("🔍 Descubriendo TODAS las páginas del sitio...")
        
        pages_to_visit = [self.base_url]
        visited_pages = set()
        all_article_urls = set()
        
        while pages_to_visit and len(visited_pages) < self.max_pages_to_explore:
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
                    if link not in visited_pages and link not in pages_to_visit:
                        if len(visited_pages) + len(pages_to_visit) >= self.max_pages_to_explore:
                            break
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
                            if len(visited_pages) + len(pages_to_visit) >= self.max_pages_to_explore:
                                break
                            pages_to_visit.append(full_url)
                
                time.sleep(1)  # Pausa entre requests
                
            except Exception as e:
                print(f"Error explorando {current_page}: {str(e)}")
                continue
        
        if pages_to_visit:
            print(f"⚠️  Límite de {self.max_pages_to_explore} páginas alcanzado. Se detuvo la exploración adicional.")

        print(f"✅ Descubrimiento completado. {len(all_article_urls)} artículos encontrados tras explorar {len(visited_pages)} páginas")
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
        print("🚀 Iniciando scraping COMPLETO de Los Andes...")
        
        # Descubrir TODAS las páginas y artículos
        all_article_urls = self.discover_pages()
        
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
                if completed % 5 == 0:
                    print(f"🔄 Progreso: {completed}/{len(all_article_urls)} artículos procesados")
                
                # Pausa entre requests
                time.sleep(0.5)
        
        print(f"🎉 Scraping completado! {len(self.all_news)} noticias extraídas")
        return self.all_news
    
    def save_to_csv(self, filename=None):
        """Guarda los datos en formato CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_folder}/losandes_{timestamp}.csv"
        
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
            filename = f"{self.data_folder}/losandes_{timestamp}.json"
        
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
    print("🚀 Iniciando scraping de Los Andes...")
    print("=" * 50)
    
    scraper = LosAndesLocalScraper()
    
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

    def save_to_files(self, articles, csv_file, json_file):
        """Guardar artículos en archivos CSV y JSON"""
        import json

        import pandas as pd

        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(csv_file), exist_ok=True)
        
        # Guardar CSV
        df = pd.DataFrame(articles)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # Guardar JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
