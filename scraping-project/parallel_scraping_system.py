#!/usr/bin/env python3
"""
Sistema de scraping paralelo con 4 hilos
Cada fuente se ejecuta en un hilo separado
"""

import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import psycopg2

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de fuentes
NEWS_SOURCES = {
    'losandes': {
        'name': 'Los Andes',
        'enabled': True,
        'priority': 1,
        'spider_module': 'spiders.losandes_local'
    },
    'punonoticias': {
        'name': 'Puno Noticias',
        'enabled': True,
        'priority': 2,
        'spider_module': 'spiders.punonoticias_local'
    },
    'pachamamaradio': {
        'name': 'Pachamama Radio',
        'enabled': True,
        'priority': 3,
        'spider_module': 'spiders.pachamamaradio_local'
    },
    'sinfronteras': {
        'name': 'Sin Fronteras',
        'enabled': True,
        'priority': 4,
        'spider_module': 'spiders.sinfronteras_local'
    }
}

# Configuración de base de datos
DB_CONFIG = {
    'host': 'postgres',
    'port': '5432',
    'database': 'noticias',
    'user': 'postgres',
    'password': '123456'
}

class ParallelScrapingSystem:
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.running = False
        self.last_scraping_times = {}
        self.scraping_interval_hours = 1  # Scraping cada hora
        
    def get_db_connection(self):
        """Obtener conexión a la base de datos"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            logger.error(f"❌ Error conectando a DB: {e}")
            return None
    
    def create_table_if_not_exists(self):
        """Crear tabla si no existe"""
        conn = self.get_db_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS noticias (
                id SERIAL PRIMARY KEY,
                titulo TEXT,
                fecha TIMESTAMP,
                hora TIME,
                resumen TEXT,
                contenido TEXT,
                categoria VARCHAR(200),
                autor VARCHAR(500),
                tags TEXT,
                url TEXT UNIQUE,
                fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                imagenes TEXT,
                fuente VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_table_query)
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ Tabla 'noticias' verificada/creada")
            return True
        except Exception as e:
            logger.error(f"❌ Error creando tabla: {e}")
            return False
    
    def scrape_single_source(self, source_key, source_config):
        """Scraping de una fuente específica en un hilo separado"""
        thread_name = threading.current_thread().name
        logger.info(f"🕷️ [{thread_name}] Iniciando scraping de {source_config['name']}")
        
        try:
            # Importar el scraper correspondiente
            if source_key == 'pachamamaradio':
                from spiders.pachamamaradio_local import \
                    PachamamaRadioLocalScraper
                scraper = PachamamaRadioLocalScraper()
            elif source_key == 'punonoticias':
                from spiders.punonoticias_local import PunoNoticiasLocalScraper
                scraper = PunoNoticiasLocalScraper()
            elif source_key == 'sinfronteras':
                from spiders.sinfronteras_local import SinFronterasLocalScraper
                scraper = SinFronterasLocalScraper()
            elif source_key == 'losandes':
                from spiders.losandes_local import LosAndesLocalScraper
                scraper = LosAndesLocalScraper()
            else:
                raise ValueError(f"Fuente no reconocida: {source_key}")
            
            # Configurar scraper para procesar pocas páginas
            scraper.max_pages = 3  # Solo 3 páginas por ejecución
            
            # Ejecutar scraping
            articles = scraper.scrape_news()
            
            if not articles:
                logger.warning(f"⚠️ [{thread_name}] No se extrajeron artículos de {source_config['name']}")
                return {
                    'source': source_key,
                    'status': 'success',
                    'migrated_count': 0,
                    'thread': thread_name
                }
            
            # Guardar en base de datos directamente
            migrated_count = self.save_articles_to_db(articles, source_key)
            
            logger.info(f"✅ [{thread_name}] {source_config['name']}: {migrated_count} artículos migrados")
            
            # Actualizar tiempo de último scraping
            self.last_scraping_times[source_key] = datetime.now()
            
            return {
                'source': source_key,
                'status': 'success',
                'migrated_count': migrated_count,
                'thread': thread_name
            }
                
        except Exception as e:
            logger.error(f"❌ [{thread_name}] Error en {source_config['name']}: {e}")
            return {
                'source': source_key,
                'status': 'error',
                'error': str(e),
                'thread': thread_name
            }
    
    def save_articles_to_db(self, articles, source_key):
        """Guardar artículos directamente en la base de datos"""
        conn = self.get_db_connection()
        if not conn:
            return 0
            
        try:
            cursor = conn.cursor()
            saved_count = 0
            
            for article in articles:
                try:
                    # Verificar duplicados
                    cursor.execute("SELECT id FROM noticias WHERE url = %s", (article['url'],))
                    if cursor.fetchone():
                        continue  # Saltar duplicados
                    
                    # Insertar registro
                    cursor.execute("""
                    INSERT INTO noticias (
                        titulo, fecha, hora, resumen, contenido, categoria, autor, 
                        tags, url, fecha_extraccion, imagenes, fuente, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
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
                    logger.warning(f"⚠️ Error guardando artículo: {e}")
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Error guardando artículos: {e}")
            return 0
    
    def migrate_to_database(self, csv_file, json_file, source_key):
        """Migrar datos a la base de datos"""
        conn = self.get_db_connection()
        if not conn:
            return 0
            
        try:
            cursor = conn.cursor()
            migrated_count = 0
            
            # Migrar desde CSV
            if csv_file and os.path.exists(csv_file):
                migrated_count += self.migrate_from_csv(cursor, conn, csv_file, source_key)
            
            # Migrar desde JSON
            if json_file and os.path.exists(json_file):
                migrated_count += self.migrate_from_json(cursor, conn, json_file, source_key)
            
            conn.close()
            return migrated_count
            
        except Exception as e:
            logger.error(f"❌ Error migrando {source_key}: {e}")
            return 0
    
    def migrate_from_csv(self, cursor, conn, csv_file, source_key):
        """Migrar datos desde archivo CSV"""
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            migrated_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Verificar duplicados
                    cursor.execute("SELECT id FROM noticias WHERE url = %s", (row['url'],))
                    if cursor.fetchone():
                        continue  # Saltar duplicados
                    
                    # Insertar registro
                    insert_query = """
                    INSERT INTO noticias (
                        titulo, fecha, hora, resumen, contenido, categoria, autor, 
                        tags, url, fecha_extraccion, imagenes, fuente, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """
                    
                    values = (
                        row.get('titulo'),
                        row.get('fecha'),
                        row.get('hora'),
                        row.get('resumen'),
                        row.get('contenido'),
                        row.get('categoria'),
                        row.get('autor'),
                        row.get('tags'),
                        row.get('url'),
                        row.get('fecha_extraccion'),
                        row.get('imagenes'),
                        row.get('fuente', source_key.title()),
                        row.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    )
                    
                    cursor.execute(insert_query, values)
                    conn.commit()
                    migrated_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error en registro CSV {index}: {e}")
                    conn.rollback()
                    continue
            
            return migrated_count
            
        except Exception as e:
            logger.error(f"❌ Error al migrar desde CSV: {e}")
            return 0
    
    def migrate_from_json(self, cursor, conn, json_file, source_key):
        """Migrar datos desde archivo JSON"""
        try:
            import json
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            migrated_count = 0
            
            for item in data:
                try:
                    # Verificar duplicados
                    cursor.execute("SELECT id FROM noticias WHERE url = %s", (item['url'],))
                    if cursor.fetchone():
                        continue  # Saltar duplicados
                    
                    # Insertar registro
                    insert_query = """
                    INSERT INTO noticias (
                        titulo, fecha, hora, resumen, contenido, categoria, autor, 
                        tags, url, fecha_extraccion, imagenes, fuente, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """
                    
                    values = (
                        item.get('titulo'),
                        item.get('fecha'),
                        item.get('hora'),
                        item.get('resumen'),
                        item.get('contenido'),
                        item.get('categoria'),
                        item.get('autor'),
                        item.get('tags'),
                        item.get('url'),
                        item.get('fecha_extraccion'),
                        item.get('imagenes'),
                        item.get('fuente', source_key.title()),
                        item.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    )
                    
                    cursor.execute(insert_query, values)
                    conn.commit()
                    migrated_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error en registro JSON: {e}")
                    conn.rollback()
                    continue
            
            return migrated_count
            
        except Exception as e:
            logger.error(f"❌ Error al migrar desde JSON: {e}")
            return 0
    
    def should_scrape_source(self, source_key):
        """Verificar si una fuente debe ser scrapeada"""
        if source_key not in self.last_scraping_times:
            return True  # Primera vez
        
        last_time = self.last_scraping_times[source_key]
        time_diff = datetime.now() - last_time
        
        # Scraping cada hora
        return time_diff >= timedelta(hours=self.scraping_interval_hours)
    
    def run_parallel_scraping(self):
        """Ejecutar scraping paralelo de todas las fuentes"""
        logger.info("🚀 Iniciando scraping paralelo con 4 hilos")
        
        # Crear tabla si no existe
        self.create_table_if_not_exists()
        
        # Filtrar fuentes que necesitan scraping
        sources_to_scrape = []
        for source_key, source_config in NEWS_SOURCES.items():
            if source_config['enabled'] and self.should_scrape_source(source_key):
                sources_to_scrape.append((source_key, source_config))
        
        if not sources_to_scrape:
            logger.info("⏰ Todas las fuentes están actualizadas, esperando...")
            return
        
        logger.info(f"📰 Scraping {len(sources_to_scrape)} fuentes en paralelo")
        
        # Ejecutar scraping en paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar tareas
            future_to_source = {
                executor.submit(self.scrape_single_source, source_key, source_config): source_key
                for source_key, source_config in sources_to_scrape
            }
            
            # Procesar resultados
            results = []
            for future in as_completed(future_to_source):
                source_key = future_to_source[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"❌ Error en {source_key}: {e}")
                    results.append({
                        'source': source_key,
                        'status': 'error',
                        'error': str(e)
                    })
        
        # Resumen de resultados
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']
        
        logger.info(f"🎉 Scraping paralelo completado:")
        logger.info(f"   ✅ Exitosos: {len(successful)}")
        logger.info(f"   ❌ Fallidos: {len(failed)}")
        
        for result in successful:
            logger.info(f"   - {result['source']}: {result['migrated_count']} artículos")
        
        for result in failed:
            logger.error(f"   - {result['source']}: {result['error']}")
    
    def run_continuous_scraping(self):
        """Ejecutar scraping continuo"""
        logger.info("🔄 Iniciando scraping continuo cada hora")
        self.running = True
        
        while self.running:
            try:
                self.run_parallel_scraping()
                
                # Esperar 1 hora antes del siguiente ciclo
                logger.info("⏰ Esperando 1 hora para el siguiente scraping...")
                time.sleep(3600)  # 1 hora
                
            except KeyboardInterrupt:
                logger.info("🛑 Deteniendo scraping continuo...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Error en scraping continuo: {e}")
                time.sleep(300)  # Esperar 5 minutos antes de reintentar
    
    def stop(self):
        """Detener el sistema"""
        self.running = False

def main():
    """Función principal"""
    logger.info("🚀 Iniciando Sistema de Scraping Paralelo")
    logger.info("=" * 60)
    
    # Crear sistema
    scraping_system = ParallelScrapingSystem(max_workers=4)
    
    try:
        # Ejecutar scraping continuo
        scraping_system.run_continuous_scraping()
    except KeyboardInterrupt:
        logger.info("🛑 Sistema detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
    finally:
        scraping_system.stop()

if __name__ == "__main__":
    main()
