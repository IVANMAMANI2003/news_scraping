#!/usr/bin/env python3
"""
Spider local para Pachamama Radio - Adaptado desde Colab
Extrae noticias y las guarda en CSV/JSON en la carpeta data/pachamamaradio
"""

import json
import logging
import os
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


class PachamamaRadioLocalScraper:
    def __init__(self):
        self.base_url = "https://pachamamaradio.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.articles_data = []
        self.visited_urls = set()
        
        # Crear carpeta de datos si no existe
        self.data_folder = "data/pachamamaradio"
        os.makedirs(self.data_folder, exist_ok=True)
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def get_page_content(self, url, retries=3):
        """Obtiene el contenido HTML de una página con reintentos"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                self.logger.error(f"Error en intento {attempt + 1} para {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    self.logger.error(f"No se pudo acceder a {url} después de {retries} intentos")
                    return None
    
    def extract_article_links_from_home(self):
        """Extrae todos los enlaces de artículos de la página principal"""
        soup = self.get_page_content(self.base_url)
        if not soup:
            return []
        
        article_links = set()
        
        # Buscar enlaces en diferentes contenedores
        selectors = [
            'a[href*="pachamamaradio.org/"][href!="#"]',
            '.entry-title a',
            '.post-title a',
            'article a',
            '.news-item a',
            '.post a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and self.is_valid_article_url(href):
                    full_url = urljoin(self.base_url, href)
                    article_links.add(full_url)
        
        return list(article_links)
    
    def find_archive_pages(self):
        """Encuentra TODAS las páginas de archivo"""
        archive_urls = set()
        
        # URLs base de categorías conocidas
        category_bases = [
            f"{self.base_url}/seccion/puno/",
            f"{self.base_url}/seccion/nacional/",
            f"{self.base_url}/seccion/internacional/",
            f"{self.base_url}/seccion/deportes/",
            f"{self.base_url}/seccion/cultura/"
        ]
        
        # Agregar páginas numeradas
        for i in range(1, 500):  # Hasta 500 páginas
            archive_urls.add(f"{self.base_url}/page/{i}/")
        
        # Buscar subcategorías específicas encontradas
        subcategories = [
            "juliaca", "azangaro", "huancane", "san-roman", "melgar", "lampa",
            "chucuito", "yunguyo", "carabaya", "sandia", "moho", "el-collao",
            "politica", "economia", "salud", "educacion", "tecnologia", "turismo"
        ]
        
        for subcat in subcategories:
            for i in range(1, 100):  # Hasta 100 páginas por subcategoría
                archive_urls.add(f"{self.base_url}/seccion/puno/{subcat}/page/{i}/")
                archive_urls.add(f"{self.base_url}/tag/{subcat}/page/{i}/")
        
        return list(archive_urls)
    
    def extract_articles_from_archive(self, archive_url):
        """Extrae enlaces de artículos de una página de archivo"""
        soup = self.get_page_content(archive_url)
        if not soup:
            return []
        
        article_links = set()
        
        # Selectores para diferentes tipos de listas de artículos
        selectors = [
            'a[href*="pachamamaradio.org/"][href!="#"]',
            '.post-title a',
            '.entry-title a',
            'article a',
            'h2 a',
            'h3 a',
            '.post-header a',
            '.news-title a'
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and self.is_valid_article_url(href):
                    full_url = urljoin(self.base_url, href)
                    article_links.add(full_url)
        
        return list(article_links)
    
    def is_valid_article_url(self, url):
        """Verifica si una URL es de un artículo válido"""
        if not url:
            return False
            
        # Excluir URLs que no son artículos
        exclude_patterns = [
            '/seccion/', '/tag/', '/category/', '/page/', '/wp-', '/feed',
            '.jpg', '.png', '.pdf', '.mp3', '.mp4', '#', 'javascript:',
            '/author/', '/search/', '/contact', '/about', 'mailto:'
        ]
        
        for pattern in exclude_patterns:
            if pattern in url.lower():
                return False
        
        # Debe contener el dominio base
        return 'pachamamaradio.org' in url and len(url.split('/')) > 3
    
    def extract_article_data(self, url):
        """Extrae todos los datos de un artículo"""
        if url in self.visited_urls:
            return None
            
        self.visited_urls.add(url)
        soup = self.get_page_content(url)
        
        if not soup:
            return None
        
        try:
            # Extraer título
            titulo = self.extract_title(soup)
            if not titulo:
                return None
            
            # Extraer datos básicos
            fecha = self.extract_date(soup)
            hora = self.extract_time(soup)
            contenido = self.extract_content(soup)
            resumen = self.extract_summary(soup, contenido)
            categoria = self.extract_category(soup, url)
            autor = self.extract_author(soup)
            tags = self.extract_tags(soup)
            imagenes = self.extract_images(soup)
            
            article_data = {
                'titulo': titulo,
                'fecha': fecha,
                'hora': hora,
                'resumen': resumen,
                'contenido': contenido,
                'categoria': categoria,
                'autor': autor,
                'tags': ', '.join(tags) if tags else None,
                'url': url,
                'fecha_extraccion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'imagenes': ', '.join(imagenes) if imagenes else None,
                'fuente': 'Pachamama Radio'
            }
            
            self.logger.info(f"Extraído: {titulo[:50]}...")
            return article_data
            
        except Exception as e:
            self.logger.error(f"Error extrayendo datos de {url}: {e}")
            return None
    
    def extract_title(self, soup):
        """Extrae el título del artículo"""
        selectors = [
            'h1.entry-title',
            'h1.post-title',
            '.single-title h1',
            'article h1',
            'h1',
            '.title h1',
            '.entry-header h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        # Fallback al título de la página
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            # Limpiar el título removiendo el nombre del sitio
            return title_text.replace(' – Pachamama Radio', '').replace(' | Pachamama Radio', '')
        
        return None
    
    def extract_date(self, soup):
        """Extrae la fecha de publicación"""
        # Buscar en diferentes selectores
        date_selectors = [
            'time[datetime]',
            '.entry-date',
            '.post-date',
            '.published',
            '[datetime]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                datetime_attr = element.get('datetime')
                if datetime_attr:
                    try:
                        return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                    except:
                        pass
                
                text_date = element.get_text(strip=True)
                if text_date:
                    return self.parse_date_text(text_date)
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def extract_time(self, soup):
        """Extrae la hora de publicación"""
        time_selectors = [
            'time[datetime]',
            '.entry-time',
            '.post-time'
        ]
        
        for selector in time_selectors:
            element = soup.select_one(selector)
            if element:
                datetime_attr = element.get('datetime')
                if datetime_attr:
                    try:
                        return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00')).strftime('%H:%M:%S')
                    except:
                        pass
        
        return datetime.now().strftime('%H:%M:%S')
    
    def parse_date_text(self, date_text):
        """Convierte texto de fecha a formato estándar"""
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
    
    def extract_content(self, soup):
        """Extrae el contenido completo del artículo"""
        content_selectors = [
            '.entry-content',
            '.post-content',
            'article .content',
            '.single-content',
            '[class*="content"]',
            'article p'
        ]
        
        content_text = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Remover scripts y estilos
                for script in element(["script", "style"]):
                    script.decompose()
                
                text = element.get_text(separator=' ', strip=True)
                if len(text) > len(content_text):
                    content_text = text
        
        return content_text if content_text else "Contenido no disponible"
    
    def extract_summary(self, soup, content):
        """Extrae o genera un resumen del artículo"""
        # Buscar resumen explícito
        summary_selectors = [
            '.excerpt',
            '.entry-summary',
            '.post-excerpt',
            'meta[name="description"]'
        ]
        
        for selector in summary_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)
        
        # Generar resumen de las primeras líneas del contenido
        if content and len(content) > 100:
            sentences = content.split('. ')[:2]
            return '. '.join(sentences) + '.' if sentences else content[:200] + '...'
        
        return content[:200] + '...' if content else "Resumen no disponible"
    
    def extract_category(self, soup, url):
        """Extrae la categoría del artículo"""
        # Buscar en breadcrumbs y categorías
        category_selectors = [
            '.category',
            '.post-category',
            '.entry-category',
            '.breadcrumb a',
            'meta[property="article:section"]'
        ]
        
        for selector in category_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)
        
        # Extraer de la URL
        url_parts = url.split('/')
        for part in url_parts:
            if part in ['puno', 'nacional', 'internacional', 'deportes', 'cultura', 'politica']:
                return part.capitalize()
        
        return "General"
    
    def extract_author(self, soup):
        """Extrae el autor del artículo"""
        author_selectors = [
            '.author',
            '.post-author',
            '.entry-author',
            '[rel="author"]',
            'meta[name="author"]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '').strip()
                return element.get_text(strip=True)
        
        return "Redacción Pachamama Radio"
    
    def extract_tags(self, soup):
        """Extrae las etiquetas del artículo"""
        tags = []
        tag_selectors = [
            '.tag',
            '.post-tag',
            '.entry-tags a',
            'meta[property="article:tag"]'
        ]
        
        for selector in tag_selectors:
            elements = soup.select(selector)
            for element in elements:
                if element.name == 'meta':
                    tags.append(element.get('content', '').strip())
                else:
                    tag_text = element.get_text(strip=True)
                    if tag_text:
                        tags.append(tag_text)
        
        return list(set(tags)) if tags else []
    
    def extract_images(self, soup):
        """Extrae las URLs de las imágenes del artículo"""
        images = []
        img_elements = soup.find_all('img')
        
        for img in img_elements:
            src = img.get('src') or img.get('data-src')
            if src:
                full_url = urljoin(self.base_url, src)
                if full_url not in images:
                    images.append(full_url)
        
        return images
    
    def scrape_news(self):
        """Scraping COMPLETO de noticias"""
        self.logger.info("Iniciando scraping COMPLETO de Pachamama Radio...")
        
        # 1. Obtener enlaces de la página principal
        self.logger.info("Extrayendo enlaces de la página principal...")
        home_links = self.extract_article_links_from_home()
        all_article_links = set(home_links)
        self.logger.info(f"Enlaces encontrados en home: {len(home_links)}")
        
        # 2. Buscar en TODAS las páginas de archivo
        self.logger.info("Buscando en TODAS las páginas de archivo...")
        archive_pages = self.find_archive_pages()
        
        for i, archive_url in enumerate(archive_pages):
            if i % 50 == 0:
                self.logger.info(f"Procesando página de archivo {i+1}/{len(archive_pages)}")
            
            archive_links = self.extract_articles_from_archive(archive_url)
            all_article_links.update(archive_links)
            
            # Pausa entre peticiones
            time.sleep(1)
            
            # Si no encuentra artículos nuevos en varias páginas consecutivas, detener
            if i > 10 and not archive_links:
                break
        
        self.logger.info(f"Total de enlaces de artículos a procesar: {len(all_article_links)}")
        
        # 3. Extraer datos de cada artículo
        self.logger.info("Extrayendo datos de cada artículo...")
        for i, article_url in enumerate(all_article_links):
            if i % 10 == 0:
                self.logger.info(f"Procesado {i}/{len(all_article_links)} artículos")
            
            article_data = self.extract_article_data(article_url)
            if article_data:
                self.articles_data.append(article_data)
                print(f"  ✅ Extraído: {article_data['titulo'][:50]}...")
            else:
                print(f"  ❌ No se pudo extraer datos")
            
            # Pausa entre artículos
            time.sleep(0.5)
        
        self.logger.info(f"Scraping completado. Total de artículos extraídos: {len(self.articles_data)}")
        return self.articles_data
    
    def save_to_csv(self, filename=None):
        """Guarda los datos en formato CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_folder}/pachamamaradio_{timestamp}.csv"
        
        if self.articles_data:
            df = pd.DataFrame(self.articles_data)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Datos guardados en {filename}")
            return filename
        else:
            print("❌ No hay datos para guardar")
            return None
    
    def save_to_json(self, filename=None):
        """Guarda los datos en formato JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_folder}/pachamamaradio_{timestamp}.json"
        
        if self.articles_data:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.articles_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Datos guardados en {filename}")
            return filename
        else:
            print("❌ No hay datos para guardar")
            return None

# Función principal para ejecutar
def main():
    print("🚀 Iniciando scraping de Pachamama Radio...")
    print("=" * 50)
    
    scraper = PachamamaRadioLocalScraper()
    
    # Realizar scraping COMPLETO
    news_data = scraper.scrape_news()
    
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
