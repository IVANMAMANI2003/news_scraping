#!/usr/bin/env python3
"""
Script simple para iniciar el sistema Docker
"""

import os
import subprocess
import time

import psycopg2


def wait_for_postgres():
    """Esperar a que PostgreSQL esté listo"""
    print("🔄 Esperando que PostgreSQL esté listo...")
    
    for i in range(30):
        try:
            conn = psycopg2.connect(
                host='news_postgres_prod',
                port=5432,
                user='postgres',
                password='123456',
                database='noticias'
            )
            conn.close()
            print("✅ PostgreSQL conectado")
            return True
        except psycopg2.OperationalError:
            print(f"⏳ Intento {i+1}/30 - Esperando PostgreSQL...")
            time.sleep(2)
    
    print("❌ No se pudo conectar a PostgreSQL")
    return False

def create_table():
    """Crear tabla si no existe"""
    try:
        conn = psycopg2.connect(
            host='news_postgres_prod',
            port=5432,
            user='postgres',
            password='123456',
            database='noticias'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Crear tabla noticias
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS noticias (
            id SERIAL PRIMARY KEY,
            titulo TEXT,
            fecha TIMESTAMP,
            hora TIME,
            resumen TEXT,
            contenido TEXT,
            categoria VARCHAR(100),
            autor VARCHAR(200),
            tags TEXT,
            url TEXT UNIQUE,
            fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            imagenes TEXT,
            fuente VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_sql)
        print("✅ Tabla 'noticias' creada/verificada")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creando tabla: {e}")
        return False

def run_simple_scraping():
    """Ejecutar scraping simple de una fuente"""
    print("🚀 Iniciando scraping simple...")
    
    try:
        # Ejecutar scraping de Pachamama Radio (solo 5 páginas para prueba)
        from spiders.pachamamaradio_local import PachamamaRadioLocalScraper
        
        scraper = PachamamaRadioLocalScraper()
        print("🕷️  Ejecutando scraping de Pachamama Radio (5 páginas)...")
        
        # Limitar a 5 páginas para prueba
        scraper.max_pages = 5
        scraper.scrape_news()
        
        print("✅ Scraping completado")
        return True
        
    except Exception as e:
        print(f"❌ Error en scraping: {e}")
        return False

def main():
    """Función principal"""
    print("🐳 SISTEMA DOCKER SIMPLE")
    print("=" * 50)
    
    # Esperar PostgreSQL
    if not wait_for_postgres():
        return
    
    # Crear tabla
    if not create_table():
        return
    
    # Ejecutar scraping simple
    if not run_simple_scraping():
        return
    
    print("\n🎉 ¡Sistema iniciado correctamente!")
    print("📊 Verifica la base de datos para ver los datos extraídos")

if __name__ == "__main__":
    main()
