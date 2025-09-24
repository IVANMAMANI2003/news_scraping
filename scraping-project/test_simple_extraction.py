#!/usr/bin/env python3
"""
Script de prueba simple para extraer solo de la página principal
"""

import os
import time
from datetime import datetime

import psycopg2
import requests
from bs4 import BeautifulSoup


def connect_to_db():
    """Conectar a la base de datos"""
    try:
        conn = psycopg2.connect(
            host='news_postgres_prod',
            port=5432,
            user='postgres',
            password='123456',
            database='noticias'
        )
        return conn
    except Exception as e:
        print(f"❌ Error conectando a DB: {e}")
        return None

def extract_simple_news():
    """Extraer noticias simples de la página principal"""
    print("🕷️  Extrayendo noticias de la página principal...")
    
    try:
        # Hacer request a la página principal
        url = "https://pachamamaradio.org"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar enlaces de noticias
        news_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and ('/noticias/' in href or '/puno/' in href or '/nacional/' in href):
                if href.startswith('/'):
                    href = f"https://pachamamaradio.org{href}"
                news_links.append(href)
        
        print(f"📰 Encontrados {len(news_links)} enlaces de noticias")
        
        # Extraer datos de los primeros 5 enlaces
        articles = []
        for i, link in enumerate(news_links[:5]):
            print(f"📄 Procesando noticia {i+1}/5: {link}")
            
            try:
                article_response = requests.get(link, headers=headers, timeout=30)
                article_response.raise_for_status()
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Extraer datos básicos
                title = article_soup.find('h1')
                title = title.get_text().strip() if title else "Sin título"
                
                content = article_soup.find('div', class_='entry-content')
                content = content.get_text().strip() if content else "Sin contenido"
                
                # Crear artículo
                article = {
                    'titulo': title,
                    'fecha': datetime.now(),
                    'hora': datetime.now().time(),
                    'resumen': content[:200] + "..." if len(content) > 200 else content,
                    'contenido': content,
                    'categoria': 'General',
                    'autor': 'Pachamama Radio',
                    'tags': '',
                    'url': link,
                    'fecha_extraccion': datetime.now(),
                    'imagenes': '',
                    'fuente': 'Pachamama Radio',
                    'created_at': datetime.now()
                }
                
                articles.append(article)
                print(f"✅ Noticia extraída: {title[:50]}...")
                
            except Exception as e:
                print(f"❌ Error procesando {link}: {e}")
                continue
        
        return articles
        
    except Exception as e:
        print(f"❌ Error en extracción: {e}")
        return []

def save_to_database(articles):
    """Guardar artículos en la base de datos"""
    if not articles:
        print("❌ No hay artículos para guardar")
        return False
    
    conn = connect_to_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO noticias (titulo, fecha, hora, resumen, contenido, categoria, autor, tags, url, fecha_extraccion, imagenes, fuente, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO NOTHING
        """
        
        saved_count = 0
        for article in articles:
            try:
                cursor.execute(insert_query, (
                    article['titulo'],
                    article['fecha'],
                    article['hora'],
                    article['resumen'],
                    article['contenido'],
                    article['categoria'],
                    article['autor'],
                    article['tags'],
                    article['url'],
                    article['fecha_extraccion'],
                    article['imagenes'],
                    article['fuente'],
                    article['created_at']
                ))
                saved_count += 1
            except Exception as e:
                print(f"❌ Error guardando artículo: {e}")
                continue
        
        conn.commit()
        print(f"✅ Guardados {saved_count} artículos en la base de datos")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error guardando en DB: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 PRUEBA SIMPLE DE EXTRACCIÓN")
    print("=" * 50)
    
    # Extraer noticias
    articles = extract_simple_news()
    
    if articles:
        # Guardar en base de datos
        if save_to_database(articles):
            print("\n🎉 ¡Prueba exitosa!")
            print(f"📊 Se extrajeron y guardaron {len(articles)} noticias")
        else:
            print("\n❌ Error guardando en base de datos")
    else:
        print("\n❌ No se pudieron extraer noticias")

if __name__ == "__main__":
    main()
