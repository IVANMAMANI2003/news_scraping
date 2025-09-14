#!/usr/bin/env python3
"""
Script para iniciar el scheduler de Celery Beat
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_app import celery_app


def start_beat():
    """
    Iniciar el scheduler de Celery Beat
    """
    print("⏰ Iniciando Celery Beat Scheduler")
    print("📅 Tareas programadas:")
    print("   - Scraping cada 6 horas")
    print("   - Limpieza cada 24 horas")
    print("=" * 50)
    
    # Iniciar beat
    celery_app.control.purge()  # Limpiar colas
    celery_app.start(['beat'])

if __name__ == '__main__':
    start_beat()
