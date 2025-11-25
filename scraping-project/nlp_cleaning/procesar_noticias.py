"""
Script simplificado para procesar noticias en segundo plano.

Este script procesa noticias y las guarda en BD sin mostrar mucho output.
Ideal para ejecutar y dejar corriendo.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integrate_db import process_all_news

if __name__ == '__main__':
    print("=" * 60)
    print("PROCESAMIENTO DE NOTICIAS CON OLLAMA")
    print("=" * 60)
    print("\nEste proceso puede tardar mucho tiempo.")
    print("Puedes cerrar esta ventana y el proceso seguirá corriendo.")
    print("Los resultados se guardan automáticamente en la BD.\n")
    
    # Procesar todas las noticias de noticias_limpia
    success = process_all_news(
        source_table="noticias_limpia",  # Leer de noticias_limpia
        batch_size=1,  # Procesar una a la vez para evitar sobrecarga
        limit=None,  # Todas las noticias
        model_name="deepseek-r1:8b",
        skip_processed=True  # Omitir ya procesadas
    )
    
    if success:
        print("\n✅ Procesamiento completado exitosamente")
    else:
        print("\n❌ Hubo errores durante el procesamiento")
    
    input("\nPresiona Enter para salir...")

