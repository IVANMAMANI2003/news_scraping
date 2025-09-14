#!/usr/bin/env python3
"""
Spider local para Puno Noticias - Adaptado desde Colab
Extrae noticias y las guarda en CSV/JSON en la carpeta data/punonoticias
"""

import json
import os
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


class PunoNoticiasLocalScraper:
    def __init__(self):
        self.base_url = "https://punonoticias.pe"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.all_news = []
        self.processed_urls = set()
        
        # Crear carpeta de datos si no existe
        self.data_folder = "data/punonoticias"
        os.makedirs(self.data_folder, exist_ok=True)
        
    def get_page_content(self, url, retries=3):
        """Obtener contenido de una página con reintentos"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response
            except Exception as e:
                print(f"Error en intento {attempt + 1} para {url}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    print(f"No se pudo acceder a {url} después de {retries} intentos")
                    return None
                    
    def extract_date_from_text(self, text):
        """Extraer fecha del texto"""
        # Patrones comunes de fecha
        patterns = [
            r'(\d{1,2})\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre),?\s+(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]
        
        months = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                if 'enero' in pattern:  # Formato con nombre de mes
                    day, month_name, year = match.groups()
                    month = months.get(month_name, '01')
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                else:  # Otros formatos
                    return match.group(0)
        return None
    
    def get_all_article_links(self):
        """Obtener TODOS los enlaces de artículos del sitio"""
        article_links = set()
        
        # Obtener enlaces de la página principal
        print("Obteniendo enlaces de la página principal...")
        main_page = self.get_page_content(self.base_url)
        if main_page:
            soup = BeautifulSoup(main_page.content, 'html.parser')
            
            # Buscar enlaces de artículos
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(self.base_url, href)
                
                # Filtrar solo artículos (excluir páginas administrativas, etc.)
                if (self.base_url in full_url and 
                    not any(skip in full_url for skip in ['/wp-admin', '/wp-login', '#', 'mailto:', 'javascript:', '/categoria/', '/tag/']) and
                    full_url != self.base_url and
                    full_url != self.base_url + '/'):
                    article_links.add(full_url)
        
        # Obtener enlaces de TODAS las categorías principales
        categories = ['/categoria/nacional/', '/categoria/internacional/', '/categoria/deportes/', 
                     '/categoria/puno/', '/categoria/politica/', '/categoria/economia/']
        
        for cat in categories:
            print(f"Obteniendo enlaces de categoría: {cat}")
            cat_url = self.base_url + cat
            page = self.get_page_content(cat_url)
            if page:
                soup = BeautifulSoup(page.content, 'html.parser')
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(self.base_url, href)
                    
                    if (self.base_url in full_url and 
                        not any(skip in full_url for skip in ['/wp-admin', '/wp-login', '#', 'mailto:', 'javascript:', '/categoria/', '/tag/']) and
                        full_url != self.base_url and
                        full_url != self.base_url + '/'):
                        article_links.add(full_url)
        
        # Obtener enlaces de páginas de archivo y paginación
        print("Buscando TODAS las páginas...")
        for page_num in range(2, 100):  # Buscar hasta 100 páginas
            page_url = f"{self.base_url}/page/{page_num}/"
            page = self.get_page_content(page_url)
            if page and page.status_code == 200:
                soup = BeautifulSoup(page.content, 'html.parser')
                found_links = False
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(self.base_url, href)
                    
                    if (self.base_url in full_url and 
                        not any(skip in full_url for skip in ['/wp-admin', '/wp-login', '#', 'mailto:', 'javascript:', '/categoria/', '/tag/']) and
                        full_url != self.base_url and
                        full_url != self.base_url + '/'):
                        article_links.add(full_url)
                        found_links = True
                
                if not found_links:
                    break
            else:
                break
        
        print(f"Total de enlaces encontrados: {len(article_links)}")
        return list(article_links)
    
    def extract_article_data(self, url):
        """Extraer datos completos de un artículo"""
        if url in self.processed_urls:
            return None
            
        self.processed_urls.add(url)
        
        page = self.get_page_content(url)
        if not page:
            return None
        
        soup = BeautifulSoup(page.content, 'html.parser')
        
        # Extraer datos
        article_data = {
            'titulo': None,
            'fecha': None,
            'hora': None,
            'resumen': None,
            'contenido': None,
            'categoria': None,
            'autor': None,
            'tags': None,
            'url': url,
            'fecha_extraccion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'imagenes': None,
            'fuente': 'Puno Noticias',
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Título
        title_selectors = [
            'h1.entry-title',
            'h1.post-title',
            'h1.article-title',
            'h1',
            '.entry-title',
            '.post-title',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                article_data['titulo'] = title_elem.get_text().strip()
                break
        
        # Si no se encuentra título en los selectores, usar el title de la página
        if not article_data['titulo']:
            page_title = soup.find('title')
            if page_title:
                article_data['titulo'] = page_title.get_text().replace(' - Puno Noticias', '').strip()
        
        # Fecha y hora
        date_selectors = [
            '.entry-date',
            '.post-date',
            '.published',
            '.date',
            'time',
            '.entry-meta'
        ]
        
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_text = date_elem.get_text().strip()
                extracted_date = self.extract_date_from_text(date_text)
                if extracted_date:
                    article_data['fecha'] = extracted_date
                    # Intentar extraer hora
                    time_match = re.search(r'(\d{1,2}):(\d{2})', date_text)
                    if time_match:
                        article_data['hora'] = time_match.group(0)
                    break
        
        # Contenido completo
        content_selectors = [
            '.entry-content',
            '.post-content',
            '.article-content',
            '.content',
            'article'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Limpiar scripts y estilos
                for script in content_elem(["script", "style"]):
                    script.decompose()
                article_data['contenido'] = content_elem.get_text().strip()
                break
        
        # Resumen (primeros 200 caracteres del contenido si no hay excerpt)
        excerpt_selectors = ['.entry-summary', '.post-excerpt', '.excerpt']
        
        for selector in excerpt_selectors:
            excerpt_elem = soup.select_one(selector)
            if excerpt_elem:
                article_data['resumen'] = excerpt_elem.get_text().strip()
                break
        
        if not article_data['resumen'] and article_data['contenido']:
            article_data['resumen'] = article_data['contenido'][:200] + "..." if len(article_data['contenido']) > 200 else article_data['contenido']
        
        # Categoría
        category_selectors = [
            '.entry-categories a',
            '.post-categories a',
            '.category a',
            '.categories a'
        ]
        
        categories = []
        for selector in category_selectors:
            cat_elems = soup.select(selector)
            for cat_elem in cat_elems:
                categories.append(cat_elem.get_text().strip())
        
        article_data['categoria'] = ', '.join(categories) if categories else None
        
        # Autor
        author_selectors = [
            '.author a',
            '.entry-author a',
            '.post-author a',
            '.by-author',
            '.author-name'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                article_data['autor'] = author_elem.get_text().strip()
                break
        
        # Tags
        tag_selectors = [
            '.entry-tags a',
            '.post-tags a',
            '.tags a',
            '.tag a'
        ]
        
        tags = []
        for selector in tag_selectors:
            tag_elems = soup.select(selector)
            for tag_elem in tag_elems:
                tags.append(tag_elem.get_text().strip())
        
        article_data['tags'] = ', '.join(tags) if tags else None
        
        # Imágenes
        img_selectors = [
            '.entry-content img',
            '.post-content img',
            '.featured-image img',
            'article img',
            'img'
        ]
        
        images = []
        for selector in img_selectors:
            img_elems = soup.select(selector)
            for img in img_elems:
                src = img.get('src') or img.get('data-src')
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
                    
                    full_img_url = urljoin(url, src)
                    if full_img_url not in images:
                        images.append(full_img_url)
                        
                        # Limitar a máximo 2 imágenes
                        if len(images) >= 2:
                            break
            
            if len(images) >= 2:
                break
        
        article_data['imagenes'] = ', '.join(images) if images else None
        
        # Estadísticas del contenido
        if article_data['contenido']:
            article_data['caracteres_contenido'] = len(article_data['contenido'])
            article_data['palabras_contenido'] = len(article_data['contenido'].split())
        else:
            article_data['caracteres_contenido'] = 0
            article_data['palabras_contenido'] = 0
        
        return article_data
    
    def scrape_news(self):
        """Scraping COMPLETO de noticias"""
        print("Iniciando scraping COMPLETO de Puno Noticias...")
        
        # Obtener TODOS los enlaces de artículos
        article_links = self.get_all_article_links()
        
        print(f"Procesando {len(article_links)} artículos...")
        
        for i, url in enumerate(article_links, 1):
            print(f"Procesando artículo {i}/{len(article_links)}: {url}")
            
            article_data = self.extract_article_data(url)
            if article_data and article_data.get('titulo'):
                self.all_news.append(article_data)
                print(f"  ✅ Extraído: {article_data['titulo'][:50]}...")
            else:
                print(f"  ❌ No se pudo extraer datos")
            
            # Pausa entre requests para ser respetuoso
            time.sleep(1)
            
            # Mostrar progreso cada 10 artículos
            if i % 10 == 0:
                print(f"Progreso: {i}/{len(article_links)} artículos procesados")
        
        print(f"Scraping completado. Total de noticias extraídas: {len(self.all_news)}")
        return self.all_news
    
    def save_to_csv(self, filename=None):
        """Guardar datos en CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_folder}/puno_noticias_{timestamp}.csv"
        
        if self.all_news:
            df = pd.DataFrame(self.all_news)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Datos guardados en {filename}")
            return filename
        else:
            print("❌ No hay datos para guardar")
            return None
    
    def save_to_json(self, filename=None):
        """Guardar datos en JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_folder}/puno_noticias_{timestamp}.json"
        
        if self.all_news:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_news, f, indent=2, ensure_ascii=False)
            print(f"✅ Datos guardados en {filename}")
            return filename
        else:
            print("❌ No hay datos para guardar")
            return None

# Función principal para ejecutar
def main():
    print("🚀 Iniciando scraping de Puno Noticias...")
    print("=" * 50)
    
    scraper = PunoNoticiasLocalScraper()
    
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
        print(f"   - Promedio de caracteres por artículo: {sum(n.get('caracteres_contenido', 0) for n in news_data) // len(news_data)}")
        print(f"   - Promedio de palabras por artículo: {sum(n.get('palabras_contenido', 0) for n in news_data) // len(news_data)}")
        
        # Mostrar categorías encontradas
        categorias = set()
        for news in news_data:
            if news.get('categoria'):
                categorias.update(news['categoria'].split(', '))
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
