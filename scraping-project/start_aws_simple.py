#!/usr/bin/env python3
"""
Sistema simple para AWS - Solo scraping sin Celery
"""

import logging
import os
import time
from datetime import datetime, timedelta

import psycopg2

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/aws_simple.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def connect_to_db():
    """Conectar a la base de datos"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', '123456'),
            database=os.getenv('POSTGRES_DB', 'noticias')
        )
        return conn
    except Exception as e:
        logger.error(f"Error conectando a DB: {e}")
        return None

def scrape_source_simple(source_name):
    """Hacer scraping de una fuente específica"""
    logger.info(f"🕷️  Iniciando scraping de {source_name}")
    
    try:
        # Importar el scraper correspondiente
        if source_name == 'pachamamaradio':
            from spiders.pachamamaradio_local import PachamamaRadioLocalScraper
            scraper = PachamamaRadioLocalScraper()
        elif source_name == 'punonoticias':
            from spiders.punonoticias_local import PunoNoticiasLocalScraper
            scraper = PunoNoticiasLocalScraper()
        elif source_name == 'sinfronteras':
            from spiders.sinfronteras_local import SinFronterasLocalScraper
            scraper = SinFronterasLocalScraper()
        elif source_name == 'losandes':
            from spiders.losandes_local import LosAndesLocalScraper
            scraper = LosAndesLocalScraper()
        else:
            logger.error(f"Fuente desconocida: {source_name}")
            return False
        
        # Configurar scraper para procesar pocas páginas
        scraper.max_pages = 5  # Solo 5 páginas por ejecución
        
        # Ejecutar scraping
        articles = scraper.scrape_news()
        
        if not articles:
            logger.warning(f"No se extrajeron artículos de {source_name}")
            return False
        
        # Guardar en base de datos
        conn = connect_to_db()
        if not conn:
            return False
        
        cursor = conn.cursor()
        saved_count = 0
        
        for article in articles:
            try:
                cursor.execute("""
INSERT INTO noticias (titulo, fecha, hora, resumen, contenido, categoria, autor, tags, url, fecha_extraccion, imagenes, fuente, created_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (url) DO NOTHING
                """, (
                    article.get('titulo'),
                    article.get('fecha'),
                    article.get('hora'),
                    article.get('resumen'),
                    article.get('contenido'),
                    article.get('categoria'),
                    article.get('autor'),
                    article.get('tags'),
                    article.get('url'),
                    article.get('fecha_extraccion'),
                    article.get('imagenes'),
                    article.get('fuente'),
                    article.get('created_at')
                ))
                saved_count += 1
            except Exception as e:
                logger.error(f"Error guardando artículo: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ {source_name}: {saved_count} noticias guardadas")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en scraping de {source_name}: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 Iniciando sistema AWS simple de noticias")
    
    # Crear directorios necesarios
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Esperar a que los servicios estén listos
    logger.info("⏳ Esperando servicios...")
    time.sleep(30)
    
    # Verificar conexión a base de datos
    conn = connect_to_db()
    if not conn:
        logger.error("❌ No se pudo conectar a la base de datos")
        return
    
    conn.close()
    logger.info("✅ Base de datos conectada")
    
    # Lista de fuentes a procesar
    sources = ['pachamamaradio', 'punonoticias', 'sinfronteras', 'losandes']
    
    # Loop principal de scraping
    while True:
        logger.info("🔄 Iniciando ciclo de scraping...")
        
        for source in sources:
            try:
                scrape_source_simple(source)
                time.sleep(60)  # Esperar 1 minuto entre fuentes
            except Exception as e:
                logger.error(f"Error procesando {source}: {e}")
                continue
        
        logger.info("⏳ Esperando 2 horas para el siguiente ciclo...")
        time.sleep(7200)  # Esperar 2 horas

if __name__ == "__main__":
    main()
