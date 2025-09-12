#!/usr/bin/env python3
"""
Programador de tareas para ejecutar el scraping automáticamente
"""

import logging
import os
import subprocess
import sys
import time
from datetime import datetime

import schedule

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping_scheduler.log'),
        logging.StreamHandler()
    ]
)

def run_scraping_job():
    """Tarea programada para ejecutar el scraping"""
    logging.info("🚀 Iniciando tarea programada de scraping")
    
    try:
        # Ejecutar el script de scraping
        result = subprocess.run([
            sys.executable, 'run_scraping.py'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            logging.info("✅ Tarea de scraping completada exitosamente")
        else:
            logging.error(f"❌ Error en tarea de scraping: {result.stderr}")
            
    except Exception as e:
        logging.error(f"❌ Error inesperado en tarea programada: {e}")

def setup_schedule():
    """Configura el horario de ejecución"""
    
    # Ejecutar cada 6 horas
    schedule.every(6).hours.do(run_scraping_job)
    
    # Ejecutar todos los días a las 6:00 AM
    schedule.every().day.at("06:00").do(run_scraping_job)
    
    # Ejecutar todos los días a las 12:00 PM
    schedule.every().day.at("12:00").do(run_scraping_job)
    
    # Ejecutar todos los días a las 6:00 PM
    schedule.every().day.at("18:00").do(run_scraping_job)
    
    logging.info("📅 Horarios configurados:")
    logging.info("  - Cada 6 horas")
    logging.info("  - Diario a las 06:00")
    logging.info("  - Diario a las 12:00") 
    logging.info("  - Diario a las 18:00")

def main():
    """Función principal del programador"""
    print("⏰ Programador de Scraping de Noticias")
    print("=" * 40)
    print("Presiona Ctrl+C para detener el programador")
    print("=" * 40)
    
    setup_schedule()
    
    # Ejecutar una vez al inicio
    logging.info("🔄 Ejecutando scraping inicial...")
    run_scraping_job()
    
    # Mantener el programador ejecutándose
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto
            
    except KeyboardInterrupt:
        logging.info("⏹️  Programador detenido por el usuario")
        print("\n👋 ¡Programador detenido!")

if __name__ == "__main__":
    main()
