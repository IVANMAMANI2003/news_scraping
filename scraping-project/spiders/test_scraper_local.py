#!/usr/bin/env python3
"""
Scraper de prueba simple para verificar que el sistema funciona correctamente
Extrae noticias de ejemplo para testing
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List


class TestScraperLocal:
    """Scraper de prueba que genera datos de ejemplo"""
    
    def __init__(self):
        self.base_url = "https://test-news.example.com"
        self.all_news = []
        self.data_folder = "data/test_scraper"
        os.makedirs(self.data_folder, exist_ok=True)
        
    def scrape_news(self, limit: int = None) -> List[Dict]:
        """
        Genera noticias de ejemplo para testing
        """
        print("🚀 Iniciando scraper de prueba...")
        
        # Generar noticias de ejemplo
        example_news = [
            {
                'titulo': 'Noticia de Prueba 1 - Sistema de Scraping Funcional',
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'resumen': 'Esta es una noticia de prueba generada por el scraper de test para verificar que el sistema funciona correctamente.',
                'contenido': 'Este es el contenido completo de la noticia de prueba número 1. El scraper de prueba genera datos de ejemplo para verificar que el sistema de scraping está funcionando correctamente. Esta noticia se genera automáticamente cuando se ejecuta el scraper de prueba.',
                'categoria': 'General',
                'autor': 'Sistema de Prueba',
                'tags': 'prueba, test, scraping',
                'url': f'{self.base_url}/noticia-prueba-1',
                'imagenes': '',
                'fuente': 'Test Scraper'
            },
            {
                'titulo': 'Noticia de Prueba 2 - Verificación del Sistema',
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'resumen': 'Segunda noticia de prueba para verificar el funcionamiento del sistema de scraping.',
                'contenido': 'Este es el contenido completo de la noticia de prueba número 2. Esta noticia también se genera automáticamente para verificar que el sistema puede procesar múltiples noticias correctamente.',
                'categoria': 'Tecnología',
                'autor': 'Sistema de Prueba',
                'tags': 'prueba, test, sistema',
                'url': f'{self.base_url}/noticia-prueba-2',
                'imagenes': '',
                'fuente': 'Test Scraper'
            },
            {
                'titulo': 'Noticia de Prueba 3 - Validación de Datos',
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'resumen': 'Tercera noticia de prueba para validar que los datos se insertan correctamente en la base de datos.',
                'contenido': 'Este es el contenido completo de la noticia de prueba número 3. Esta noticia se genera para validar que el sistema puede insertar datos en la base de datos correctamente.',
                'categoria': 'General',
                'autor': 'Sistema de Prueba',
                'tags': 'prueba, validación, datos',
                'url': f'{self.base_url}/noticia-prueba-3',
                'imagenes': '',
                'fuente': 'Test Scraper'
            },
            {
                'titulo': 'Noticia de Prueba 4 - Filtros y Límites',
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'resumen': 'Cuarta noticia de prueba para verificar que los filtros y límites funcionan correctamente.',
                'contenido': 'Este es el contenido completo de la noticia de prueba número 4. Esta noticia se genera para verificar que los filtros de fecha, categoría y límites funcionan correctamente en el sistema.',
                'categoria': 'Deportes',
                'autor': 'Sistema de Prueba',
                'tags': 'prueba, filtros, límites',
                'url': f'{self.base_url}/noticia-prueba-4',
                'imagenes': '',
                'fuente': 'Test Scraper'
            },
            {
                'titulo': 'Noticia de Prueba 5 - Integración Completa',
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'resumen': 'Quinta noticia de prueba para verificar la integración completa del sistema.',
                'contenido': 'Este es el contenido completo de la noticia de prueba número 5. Esta noticia se genera para verificar que toda la integración del sistema funciona correctamente, desde el scraping hasta la inserción en la base de datos.',
                'categoria': 'Política',
                'autor': 'Sistema de Prueba',
                'tags': 'prueba, integración, sistema',
                'url': f'{self.base_url}/noticia-prueba-5',
                'imagenes': '',
                'fuente': 'Test Scraper'
            }
        ]
        
        # Aplicar límite si se especifica
        if limit:
            example_news = example_news[:limit]
        
        self.all_news = example_news
        
        print(f"✅ Scraper de prueba completado. {len(self.all_news)} noticias generadas")
        return self.all_news
    
    def save_to_json(self, filename=None):
        """Guarda los datos en formato JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.data_folder}/test_scraper_{timestamp}.json"
        
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
    print("🚀 Iniciando scraper de prueba...")
    print("=" * 50)
    
    scraper = TestScraperLocal()
    
    # Realizar scraping
    news_data = scraper.scrape_news()
    
    if news_data:
        # Guardar en JSON
        json_file = scraper.save_to_json()
        
        print(f"\n🎉 ¡Scraping de prueba completado exitosamente!")
        print(f"📊 Total de noticias generadas: {len(news_data)}")
        print(f"📁 Archivo guardado: {json_file}")
        
        return json_file
    else:
        print("❌ No se pudieron generar noticias de prueba")
        return None


if __name__ == "__main__":
    main()

