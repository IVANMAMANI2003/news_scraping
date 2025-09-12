#!/usr/bin/env python3
"""
Script de prueba simple para Puno Noticias
"""

import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def test_punonoticias_connection():
    """Probar conexión a Puno Noticias"""
    print("🔍 Probando conexión a Puno Noticias...")
    
    try:
        url = "https://punonoticias.pe"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print(f"✅ Conexión exitosa a {url}")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Tamaño de respuesta: {len(response.content)} bytes")
        
        # Probar parsing básico
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('title')
        
        if title:
            print(f"📄 Título de la página: {title.get_text()}")
        
        # Buscar algunos enlaces
        links = soup.find_all('a', href=True)[:5]
        print(f"🔗 Primeros 5 enlaces encontrados:")
        for i, link in enumerate(links, 1):
            href = link.get('href')
            text = link.get_text().strip()[:50]
            print(f"   {i}. {text}... -> {href}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_simple_scraping():
    """Probar scraping simple de un artículo"""
    print(f"\n🕷️  Probando scraping simple...")
    
    try:
        # URL de ejemplo (puedes cambiarla por una real)
        test_url = "https://punonoticias.pe"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(test_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar títulos de noticias
        titles = soup.find_all(['h1', 'h2', 'h3'])[:3]
        
        print(f"📰 Títulos encontrados:")
        for i, title in enumerate(titles, 1):
            text = title.get_text().strip()
            if text:
                print(f"   {i}. {text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en scraping: {e}")
        return False

def main():
    """Función principal"""
    print("🧪 Prueba Simple de Puno Noticias")
    print("=" * 50)
    
    # Probar conexión
    connection_ok = test_punonoticias_connection()
    
    if connection_ok:
        # Probar scraping básico
        scraping_ok = test_simple_scraping()
        
        if scraping_ok:
            print(f"\n🎉 ¡Todo funcionando correctamente!")
            print(f"✅ Puedes ejecutar el scraping completo:")
            print(f"   python spiders/punonoticias_local.py")
        else:
            print(f"\n⚠️  Hay problemas con el scraping")
    else:
        print(f"\n❌ Hay problemas de conexión")
        print(f"💡 Verifica tu conexión a internet")

if __name__ == "__main__":
    main()
