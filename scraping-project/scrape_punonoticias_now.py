#!/usr/bin/env python3
"""
Script directo para hacer scraping de Puno Noticias AHORA
"""

import json
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def scrape_punonoticias():
    """Hacer scraping de Puno Noticias"""
    print("🚀 Iniciando scraping de Puno Noticias...")
    
    # Crear carpeta de datos
    os.makedirs("data/punonoticias", exist_ok=True)
    
    # Configuración
    base_url = "https://punonoticias.pe"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Obtener página principal
        print("📄 Obteniendo página principal...")
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar enlaces de noticias
        news_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href and base_url in href and '/wp-admin' not in href:
                news_links.append(href)
        
        # Limitar a 10 enlaces para prueba
        news_links = list(set(news_links))[:10]
        print(f"🔗 Encontrados {len(news_links)} enlaces de noticias")
        
        # Extraer datos de cada noticia
        all_news = []
        
        for i, url in enumerate(news_links, 1):
            print(f"📰 Procesando {i}/{len(news_links)}: {url}")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraer datos básicos
                news_data = {
                    'url': url,
                    'titulo': '',
                    'contenido': '',
                    'fecha': '',
                    'fuente': 'Puno Noticias',
                    'fecha_extraccion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Título
                title = soup.find('h1') or soup.find('title')
                if title:
                    news_data['titulo'] = title.get_text().strip()
                
                # Contenido
                content = soup.find('article') or soup.find('.content') or soup.find('main')
                if content:
                    news_data['contenido'] = content.get_text().strip()
                
                # Fecha
                date_elem = soup.find('time') or soup.find('.date')
                if date_elem:
                    news_data['fecha'] = date_elem.get_text().strip()
                
                if news_data['titulo']:
                    all_news.append(news_data)
                    print(f"  ✅ Extraído: {news_data['titulo'][:50]}...")
                else:
                    print(f"  ❌ No se pudo extraer título")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
        
        # Guardar en JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = f"data/punonoticias/puno_noticias_{timestamp}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_news, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 ¡Scraping completado!")
        print(f"📊 Noticias extraídas: {len(all_news)}")
        print(f"📁 Archivo guardado: {json_file}")
        
        # Mostrar muestra de datos
        if all_news:
            print(f"\n📰 Muestra de datos:")
            for i, news in enumerate(all_news[:3], 1):
                print(f"  {i}. {news['titulo'][:60]}...")
        
        return json_file, len(all_news)
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return None, 0

if __name__ == "__main__":
    print("🕷️  Scraper de Puno Noticias - Versión Simple")
    print("=" * 50)
    
    json_file, count = scrape_punonoticias()
    
    if json_file:
        print(f"\n✅ ¡Proceso completado exitosamente!")
        print(f"📁 Archivo: {json_file}")
        print(f"📊 Total: {count} noticias")
        
        print(f"\n📝 Próximos pasos:")
        print(f"1. Revisa el archivo JSON generado")
        print(f"2. Ejecuta: python migrate_punonoticias_to_db.py")
        print(f"3. Verifica los datos en PostgreSQL")
    else:
        print(f"\n❌ El proceso falló")
        print(f"💡 Verifica tu conexión a internet")
