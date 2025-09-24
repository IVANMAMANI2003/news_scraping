#!/usr/bin/env python3
"""
Monitor avanzado para el sistema de scraping en AWS
"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta

import psycopg2

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AWSMonitor:
    def __init__(self):
        self.db_config = {
            'host': 'postgres',
            'port': '5432',
            'database': 'noticias',
            'user': 'postgres',
            'password': '123456'
        }
    
    def get_db_connection(self):
        """Obtener conexión a la base de datos"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"❌ Error conectando a DB: {e}")
            return None
    
    def check_system_status(self):
        """Verificar estado del sistema"""
        logger.info("🔍 Verificando estado del sistema...")
        
        # Verificar conexión a base de datos
        conn = self.get_db_connection()
        if not conn:
            logger.error("❌ Sistema: Base de datos no disponible")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Verificar tabla
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'noticias'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                logger.error("❌ Sistema: Tabla 'noticias' no existe")
                return False
            
            # Verificar datos
            cursor.execute("SELECT COUNT(*) FROM noticias")
            total_records = cursor.fetchone()[0]
            
            # Verificar datos por fuente
            cursor.execute("""
                SELECT fuente, COUNT(*) as count
                FROM noticias 
                GROUP BY fuente
                ORDER BY count DESC
            """)
            sources_data = cursor.fetchall()
            
            # Verificar actividad reciente
            yesterday = datetime.now() - timedelta(days=1)
            cursor.execute("""
                SELECT COUNT(*) FROM noticias 
                WHERE fecha_extraccion >= %s
            """, (yesterday,))
            recent_records = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            # Mostrar estado
            logger.info(f"✅ Sistema: Base de datos conectada")
            logger.info(f"📊 Total de registros: {total_records}")
            logger.info(f"🕐 Registros últimas 24h: {recent_records}")
            
            logger.info("📰 Datos por fuente:")
            for source, count in sources_data:
                logger.info(f"   - {source}: {count} registros")
            
            # Verificar si hay datos de todas las fuentes
            expected_sources = ['Los Andes', 'Puno Noticias', 'Pachamama Radio', 'Sin Fronteras']
            active_sources = [source for source, _ in sources_data]
            
            missing_sources = set(expected_sources) - set(active_sources)
            if missing_sources:
                logger.warning(f"⚠️ Fuentes faltantes: {', '.join(missing_sources)}")
            else:
                logger.info("✅ Todas las fuentes tienen datos")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verificando sistema: {e}")
            return False
    
    def check_scraping_activity(self):
        """Verificar actividad de scraping"""
        logger.info("🕷️ Verificando actividad de scraping...")
        
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Últimas extracciones por fuente
            cursor.execute("""
                SELECT 
                    fuente,
                    MAX(fecha_extraccion) as ultima_extraccion,
                    COUNT(*) as total_registros
                FROM noticias 
                GROUP BY fuente
                ORDER BY ultima_extraccion DESC
            """)
            
            sources_activity = cursor.fetchall()
            
            logger.info("📊 Actividad de scraping por fuente:")
            for source, last_extraction, total in sources_activity:
                time_diff = datetime.now() - last_extraction
                hours_ago = time_diff.total_seconds() / 3600
                
                status = "🟢" if hours_ago < 2 else "🟡" if hours_ago < 24 else "🔴"
                logger.info(f"   {status} {source}: {total} registros, última extracción hace {hours_ago:.1f} horas")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verificando actividad: {e}")
            return False
    
    def check_data_quality(self):
        """Verificar calidad de los datos"""
        logger.info("🔍 Verificando calidad de los datos...")
        
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Verificar duplicados
            cursor.execute("""
                SELECT url, COUNT(*) as count
                FROM noticias 
                GROUP BY url
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 5
            """)
            duplicates = cursor.fetchall()
            
            if duplicates:
                logger.warning(f"⚠️ Encontrados {len(duplicates)} URLs duplicadas:")
                for url, count in duplicates:
                    logger.warning(f"   - {url}: {count} veces")
            else:
                logger.info("✅ No hay URLs duplicadas")
            
            # Verificar registros con campos vacíos
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN titulo IS NULL OR titulo = '' THEN 1 END) as sin_titulo,
                    COUNT(CASE WHEN contenido IS NULL OR contenido = '' THEN 1 END) as sin_contenido,
                    COUNT(CASE WHEN url IS NULL OR url = '' THEN 1 END) as sin_url
                FROM noticias
            """)
            
            quality_data = cursor.fetchone()
            total, sin_titulo, sin_contenido, sin_url = quality_data
            
            logger.info("📊 Calidad de datos:")
            logger.info(f"   - Total registros: {total}")
            logger.info(f"   - Sin título: {sin_titulo}")
            logger.info(f"   - Sin contenido: {sin_contenido}")
            logger.info(f"   - Sin URL: {sin_url}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verificando calidad: {e}")
            return False
    
    def run_monitoring_cycle(self):
        """Ejecutar un ciclo completo de monitoreo"""
        logger.info("🔄 Iniciando ciclo de monitoreo")
        logger.info("=" * 60)
        
        # Verificar estado del sistema
        system_ok = self.check_system_status()
        
        if system_ok:
            # Verificar actividad de scraping
            self.check_scraping_activity()
            
            # Verificar calidad de datos
            self.check_data_quality()
        
        logger.info("=" * 60)
        logger.info(f"📊 Estado del sistema: {'✅ OPERATIVO' if system_ok else '❌ CON PROBLEMAS'}")
        
        return system_ok
    
    def run_continuous_monitoring(self, interval_minutes=30):
        """Ejecutar monitoreo continuo"""
        logger.info(f"🔄 Iniciando monitoreo continuo cada {interval_minutes} minutos")
        
        while True:
            try:
                self.run_monitoring_cycle()
                
                logger.info(f"⏰ Esperando {interval_minutes} minutos para el siguiente ciclo...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoreo detenido por el usuario")
                break
            except Exception as e:
                logger.error(f"❌ Error en monitoreo: {e}")
                time.sleep(60)  # Esperar 1 minuto antes de reintentar

def main():
    """Función principal"""
    logger.info("🚀 Iniciando Monitor Avanzado de AWS")
    
    monitor = AWSMonitor()
    
    try:
        # Ejecutar un ciclo de monitoreo
        monitor.run_monitoring_cycle()
        
        # Preguntar si continuar con monitoreo continuo
        response = input("\n¿Desea continuar con monitoreo continuo? (y/n): ")
        if response.lower() in ['y', 'yes', 'sí', 'si']:
            monitor.run_continuous_monitoring()
        
    except KeyboardInterrupt:
        logger.info("🛑 Monitor detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")

if __name__ == "__main__":
    main()
