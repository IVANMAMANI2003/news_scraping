import json
import logging
import re
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LosAndesScraper:
    def __init__(self):
        self.base_url = "https://losandes.com.pe"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.scraped_urls = set()
        self.articles_data = []
        self.lock = threading.Lock()
        self.categories_found = set()
        
    def get_page(self, url, retries=3):
        """Obtiene el contenido de una página con reintentos"""
        for attempt in range(retries):
            try:
                time.sleep(1)  # Delay entre requests
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Error en intento {attempt + 1} para {url}: {e}")
                if attempt == retries - 1:
                    logger.error(f"Falló completamente: {url}")
                    return None
                time.sleep(2)
        return None

    def extract_article_links(self, soup, base_url):
        """Extrae todos los links de artículos de una página"""
        links = set()
        
        # Diferentes selectores para encontrar links de artículos
        selectors = [
            'a[href*="/2024/"]',
            'a[href*="/2023/"]', 
            'a[href*="/2022/"]',
            'a[href*="/blog/"]',
            'a[href*="/actualidad/"]',
            'a[href*="/deportes/"]',
            'a[href*="/economia/"]',
            'a[href*="/cultura/"]',
            'a[href*="/politica/"]',
            'h1 a', 'h2 a', 'h3 a', 'h4 a',
            '.entry-title a',
            '.post-title a',
            '.article-title a',
            'article a',
            '.news-item a',
            '.post a[href]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    # Filtrar solo URLs que parezcan artículos
                    if self.is_article_url(full_url):
                        links.add(full_url)
        
        return links

    def is_article_url(self, url):
        """Determina si una URL es de un artículo"""
        if not url.startswith(self.base_url):
            return False
            
        # Patrones que indican que es un artículo
        article_patterns = [
            r'/\d{4}/',  # Contiene año
            r'/blog/',
            r'/actualidad/',
            r'/deportes/',
            r'/economia/',
            r'/cultura/',
            r'/politica/',
        ]
        
        # Patrones que indican que NO es un artículo
        exclude_patterns = [
            r'/tag/',
            r'/category/',
            r'/author/',
            r'/page/',
            r'/search/',
            r'\.jpg$|\.png$|\.gif$|\.pdf$',
            r'/wp-admin/',
            r'/wp-content/',
            r'/feed/',
            r'#comment',
        ]
        
        # Verificar si excluir
        for pattern in exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
                
        # Verificar si incluir
        for pattern in article_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
                
        # Si tiene un slug largo, probablemente es un artículo
        path_parts = urlparse(url).path.strip('/').split('/')
        if len(path_parts) > 1 and len(path_parts[-1]) > 10:
            return True
            
        return False

    def extract_article_data(self, url):
        """Extrae los datos de un artículo específico"""
        try:
            response = self.get_page(url)
            if not response:
                return None
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Datos básicos
            data = {
                'url': url,
                'titulo': '',
                'fecha': '',
                'hora': '',
                'resumen': '',
                'contenido': '',
                'categoria': '',
                'autor': '',
                'tags': '',
                'link_imagenes': '',
                'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Extraer título
            title_selectors = [
                'h1.entry-title',
                'h1.post-title', 
                'h1.article-title',
                '.single-title h1',
                'article h1',
                'h1',
                '.title h1',
                'header h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    data['titulo'] = title_elem.get_text(strip=True)
                    break
            
            # Extraer fecha y hora
            date_selectors = [
                'time[datetime]',
                '.entry-date',
                '.post-date',
                '.date',
                '.published',
                '[class*="date"]',
                '[class*="time"]'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    parsed_date = self.parse_date(date_text)
                    if parsed_date:
                        data['fecha'] = parsed_date.strftime('%Y-%m-%d')
                        data['hora'] = parsed_date.strftime('%H:%M:%S')
                        break
            
            # Extraer resumen/excerpt
            summary_selectors = [
                '.entry-summary',
                '.excerpt',
                '.post-excerpt',
                '.article-summary',
                'meta[name="description"]',
                '.lead'
            ]
            
            for selector in summary_selectors:
                if selector.startswith('meta'):
                    summary_elem = soup.select_one(selector)
                    if summary_elem:
                        data['resumen'] = summary_elem.get('content', '').strip()
                        break
                else:
                    summary_elem = soup.select_one(selector)
                    if summary_elem:
                        data['resumen'] = summary_elem.get_text(strip=True)
                        break
            
            # Extraer contenido principal
            content_selectors = [
                '.entry-content',
                '.post-content',
                '.article-content',
                '.content',
                'article .text',
                '.single-content',
                'main article p'
            ]
            
            content_parts = []
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remover scripts y estilos
                    for script in content_elem(["script", "style"]):
                        script.decompose()
                    
                    paragraphs = content_elem.find_all(['p', 'div'], string=True)
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if len(text) > 20:  # Solo párrafos con contenido sustancial
                            content_parts.append(text)
                    break
            
            data['contenido'] = '\n\n'.join(content_parts)
            
            # Extraer categoría
            category_selectors = [
                '.category a',
                '.cat-links a',
                '.entry-categories a',
                '[rel="category tag"]',
                '.post-categories a'
            ]
            
            categories = []
            for selector in category_selectors:
                cat_elems = soup.select(selector)
                for elem in cat_elems:
                    cat_text = elem.get_text(strip=True)
                    if cat_text and cat_text not in categories:
                        categories.append(cat_text)
            
            data['categoria'] = ', '.join(categories)
            if data['categoria']:
                self.categories_found.add(data['categoria'])
            
            # Extraer autor
            author_selectors = [
                '.author-name',
                '.entry-author',
                '.post-author',
                '[rel="author"]',
                '.by-author',
                '.author'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    data['autor'] = author_elem.get_text(strip=True)
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
                for elem in tag_elems:
                    tag_text = elem.get_text(strip=True)
                    if tag_text and tag_text not in tags:
                        tags.append(tag_text)
            
            data['tags'] = ', '.join(tags)
            
            # Extraer imágenes
            img_selectors = [
                '.entry-content img',
                '.post-content img',
                '.article-content img',
                'article img',
                '.featured-image img'
            ]
            
            images = set()
            for selector in img_selectors:
                img_elems = soup.select(selector)
                for img in img_elems:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        full_img_url = urljoin(url, src)
                        images.add(full_img_url)
            
            data['link_imagenes'] = ', '.join(list(images))
            
            logger.info(f"Extraído artículo: {data['titulo'][:50]}...")
            return data
            
        except Exception as e:
            logger.error(f"Error extrayendo artículo {url}: {e}")
            return None

    def parse_date(self, date_string):
        """Parsea diferentes formatos de fecha"""
        if not date_string:
            return None
            
        # Patrones comunes de fecha
        patterns = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%B %d, %Y',
            '%d de %B de %Y',
        ]
        
        date_string = re.sub(r'[^\w\s:/-]', '', str(date_string)).strip()
        
        for pattern in patterns:
            try:
                return datetime.strptime(date_string, pattern)
            except ValueError:
                continue
        
        return None

    def discover_pagination_urls(self, base_soup, base_url):
        """Descubre URLs de paginación"""
        pagination_urls = set()
        
        # Buscar enlaces de paginación
        pagination_selectors = [
            '.pagination a',
            '.page-numbers a',
            '.nav-links a',
            'a[href*="page"]',
            'a[href*="paged"]'
        ]
        
        for selector in pagination_selectors:
            elems = base_soup.select(selector)
            for elem in elems:
                href = elem.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    pagination_urls.add(full_url)
        
        return pagination_urls

    def discover_category_urls(self, soup, base_url):
        """Descubre URLs de categorías"""
        category_urls = set()
        
        category_selectors = [
            '.menu a',
            '.nav a',
            '.category-list a',
            '.categories a',
            '[href*="category"]'
        ]
        
        for selector in category_selectors:
            elems = soup.select(selector)
            for elem in elems:
                href = elem.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if 'category' in full_url or 'actualidad' in full_url or 'deportes' in full_url:
                        category_urls.add(full_url)
        
        return category_urls

    def crawl_all_pages(self):
        """Crawlea todas las páginas para encontrar artículos"""
        logger.info("Iniciando crawling completo de Los Andes...")
        
        # URLs iniciales para explorar
        initial_urls = [
            self.base_url,
            f"{self.base_url}/blog/",
            f"{self.base_url}/actualidad/",
            f"{self.base_url}/deportes/",
            f"{self.base_url}/economia/",
            f"{self.base_url}/cultura/",
            f"{self.base_url}/politica/",
        ]
        
        # Agregar URLs con páginas numeradas
        for i in range(1, 50):  # Explorar primeras 50 páginas
            initial_urls.extend([
                f"{self.base_url}/page/{i}/",
                f"{self.base_url}/blog/page/{i}/",
            ])
        
        urls_to_crawl = deque(initial_urls)
        crawled_pages = set()
        all_article_urls = set()
        
        # Crawlear páginas para encontrar artículos
        while urls_to_crawl:
            url = urls_to_crawl.popleft()
            
            if url in crawled_pages:
                continue
                
            logger.info(f"Crawleando página: {url}")
            
            response = self.get_page(url)
            if not response:
                continue
                
            crawled_pages.add(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Encontrar artículos en esta página
            article_links = self.extract_article_links(soup, self.base_url)
            all_article_urls.update(article_links)
            
            # Encontrar más páginas para crawlear
            pagination_urls = self.discover_pagination_urls(soup, url)
            category_urls = self.discover_category_urls(soup, url)
            
            for new_url in pagination_urls.union(category_urls):
                if new_url not in crawled_pages and new_url not in urls_to_crawl:
                    urls_to_crawl.append(new_url)
        
        logger.info(f"Descubiertos {len(all_article_urls)} artículos únicos")
        return list(all_article_urls)

    def scrape_articles_parallel(self, article_urls, max_workers=5):
        """Extrae artículos en paralelo"""
        logger.info(f"Iniciando extracción paralela de {len(article_urls)} artículos...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas
            future_to_url = {
                executor.submit(self.extract_article_data, url): url 
                for url in article_urls
            }
            
            # Recoger resultados
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    article_data = future.result()
                    if article_data:
                        with self.lock:
                            self.articles_data.append(article_data)
                            logger.info(f"Progreso: {len(self.articles_data)}/{len(article_urls)} artículos extraídos")
                except Exception as e:
                    logger.error(f"Error procesando {url}: {e}")

    def save_data(self, filename_base="losandes_noticias"):
        """Guarda los datos en CSV y JSON"""
        if not self.articles_data:
            logger.warning("No hay datos para guardar")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar como CSV
        csv_filename = f"{filename_base}_{timestamp}.csv"
        df = pd.DataFrame(self.articles_data)
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        logger.info(f"Datos guardados en CSV: {csv_filename}")
        
        # Guardar como JSON
        json_filename = f"{filename_base}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.articles_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Datos guardados en JSON: {json_filename}")
        
        # Estadísticas finales
        logger.info(f"Total de artículos extraídos: {len(self.articles_data)}")
        logger.info(f"Categorías encontradas: {len(self.categories_found)}")
        logger.info("Extracción completada exitosamente!")
        
        return csv_filename, json_filename

    def run_complete_scraping(self):
        """Ejecuta el scraping completo"""
        start_time = time.time()
        
        try:
            # 1. Descubrir todos los artículos
            article_urls = self.crawl_all_pages()
            
            if not article_urls:
                logger.error("No se encontraron artículos para extraer")
                return
            
            # 2. Extraer datos de todos los artículos
            self.scrape_articles_parallel(article_urls)
            
            # 3. Guardar datos
            self.save_data()
            
            end_time = time.time()
            logger.info(f"Tiempo total de ejecución: {end_time - start_time:.2f} segundos")
            
        except KeyboardInterrupt:
            logger.info("Scraping interrumpido por el usuario")
            if self.articles_data:
                logger.info("Guardando datos parciales...")
                self.save_data("losandes_noticias_parcial")
        except Exception as e:
            logger.error(f"Error durante el scraping: {e}")
            if self.articles_data:
                logger.info("Guardando datos parciales...")
                self.save_data("losandes_noticias_parcial")

# Ejecutar el scraper
if __name__ == "__main__":
    scraper = LosAndesScraper()
    scraper.run_complete_scraping()