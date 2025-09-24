#!/usr/bin/env python3
"""
Script de prueba para el sistema de scraping paralelo
"""

import logging
import os
import sys
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_parallel_scraping():
    """Probar el sistema de scraping paralelo"""
    logger.info("🧪 Iniciando prueba del sistema de scraping paralelo")
    
    try:
        from parallel_scraping_system import ParallelScrapingSystem

        # Crear sistema con 2 hilos para prueba
        scraping_system = ParallelScrapingSystem(max_workers=2)
        
        # Verificar conexión a base de datos
        conn = scraping_system.get_db_connection()
        if not conn:
            logger.error("❌ No se pudo conectar a la base de datos")
            return False
        
        conn.close()
        logger.info("✅ Conexión a base de datos exitosa")
        
        # Crear tabla si no existe
        if scraping_system.create_table_if_not_exists():
            logger.info("✅ Tabla verificada/creada")
        else:
            logger.error("❌ Error creando tabla")
            return False
        
        # Ejecutar una sola ronda de scraping
        logger.info("🕷️ Ejecutando prueba de scraping...")
        scraping_system.run_parallel_scraping()
        
        logger.info("✅ Prueba completada exitosamente")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Error importando sistema paralelo: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error en prueba: {e}")
        return False

def test_single_source():
    """Probar scraping de una sola fuente"""
    logger.info("🧪 Probando scraping de una sola fuente (Pachamama Radio)")
    
    try:
        from spiders.pachamamaradio_local import PachamamaRadioLocalScraper
        
        scraper = PachamamaRadioLocalScraper()
        scraper.max_pages = 1  # Solo 1 página para prueba
        
        articles = scraper.scrape_news()
        
        if articles:
            logger.info(f"✅ Extraídos {len(articles)} artículos de Pachamama Radio")
            
            # Mostrar primer artículo
            if articles:
                first_article = articles[0]
                logger.info(f"📰 Primer artículo: {first_article.get('titulo', 'Sin título')}")
                logger.info(f"🔗 URL: {first_article.get('url', 'Sin URL')}")
                logger.info(f"📅 Fecha: {first_article.get('fecha', 'Sin fecha')}")
            
            return True
        else:
            logger.warning("⚠️ No se extrajeron artículos")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en prueba de fuente única: {e}")
        return False

def main():
    """Función principal de prueba"""
    logger.info("🚀 Iniciando pruebas del sistema de scraping")
    logger.info("=" * 60)
    
    # Prueba 1: Scraping de una sola fuente
    logger.info("\n📋 Prueba 1: Scraping de una sola fuente")
    test1_result = test_single_source()
    
    # Prueba 2: Sistema paralelo
    logger.info("\n📋 Prueba 2: Sistema de scraping paralelo")
    test2_result = test_parallel_scraping()
    
    # Resumen
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMEN DE PRUEBAS:")
    logger.info(f"   - Prueba 1 (Fuente única): {'✅ PASÓ' if test1_result else '❌ FALLÓ'}")
    logger.info(f"   - Prueba 2 (Sistema paralelo): {'✅ PASÓ' if test2_result else '❌ FALLÓ'}")
    
    if test1_result and test2_result:
        logger.info("🎉 Todas las pruebas pasaron exitosamente")
        return True
    else:
        logger.error("❌ Algunas pruebas fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
