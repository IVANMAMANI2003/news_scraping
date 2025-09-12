#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del scraping
"""

import os
import subprocess
import sys
from datetime import datetime


def test_database_connection():
    """Prueba la conexión a la base de datos"""
    print("🔍 Probando conexión a PostgreSQL...")
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host="localhost",
            database="noticias",
            user="root",
            password="123456",
            port="5432"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conexión exitosa: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_spider(spider_name):
    """Prueba un spider específico"""
    print(f"🕷️  Probando spider: {spider_name}")
    
    try:
        # Ejecutar spider con límite de items
        result = subprocess.run([
            'scrapy', 'crawl', spider_name, 
            '-s', 'CLOSESPIDER_ITEMCOUNT=3',  # Solo 3 items para prueba
            '-L', 'INFO'
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ Spider {spider_name} funcionando correctamente")
            return True
        else:
            print(f"❌ Error en spider {spider_name}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout en spider {spider_name}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado en spider {spider_name}: {e}")
        return False

def test_database_data():
    """Verifica que los datos se estén guardando en la base de datos"""
    print("📊 Verificando datos en la base de datos...")
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host="localhost",
            database="noticias",
            user="root",
            password="123456",
            port="5432"
        )
        
        cursor = conn.cursor()
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM noticias;")
        count = cursor.fetchone()[0]
        print(f"📈 Total de noticias en BD: {count}")
        
        if count > 0:
            # Mostrar última noticia
            cursor.execute("""
                SELECT titulo, fuente, created_at 
                FROM noticias 
                ORDER BY created_at DESC 
                LIMIT 1;
            """)
            latest = cursor.fetchone()
            if latest:
                print(f"📰 Última noticia: {latest[0][:50]}...")
                print(f"📰 Fuente: {latest[1]}")
                print(f"📰 Fecha: {latest[2]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        return False

def main():
    """Función principal de prueba"""
    print("🧪 Pruebas del Sistema de Scraping")
    print("=" * 50)
    
    tests = [
        ("Conexión a PostgreSQL", test_database_connection),
        ("Spider Los Andes", lambda: test_spider('losandes')),
        ("Verificación de datos", test_database_data),
    ]
    
    successful = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            successful += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Resumen de pruebas:")
    print(f"✅ Exitosas: {successful}")
    print(f"❌ Fallidas: {failed}")
    
    if failed == 0:
        print("\n🎉 ¡Todas las pruebas pasaron!")
        print("✅ El sistema está funcionando correctamente")
    else:
        print(f"\n⚠️  {failed} pruebas fallaron")
        print("Revisa los mensajes de error arriba")

if __name__ == "__main__":
    main()
