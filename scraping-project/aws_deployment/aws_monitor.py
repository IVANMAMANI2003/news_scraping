#!/usr/bin/env python3
"""
Script de monitoreo para AWS
"""

import time
from datetime import datetime

import psycopg2


def connect_to_db():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='123456',
            database='noticias'
        )
        return conn
    except Exception as e:
        print(f"❌ Error conectando a DB: {e}")
        return None

def get_stats():
    """Obtener estadísticas del sistema"""
    conn = connect_to_db()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Total de noticias
    cursor.execute("SELECT COUNT(*) FROM noticias")
    total_news = cursor.fetchone()[0]
    
    # Noticias por fuente
    cursor.execute("SELECT fuente, COUNT(*) FROM noticias GROUP BY fuente")
    by_source = cursor.fetchall()
    
    # Últimas noticias
    cursor.execute("SELECT titulo, fuente, fecha_extraccion FROM noticias ORDER BY fecha_extraccion DESC LIMIT 5")
    latest_news = cursor.fetchall()
    
    # Control de scraping
    cursor.execute("SELECT fuente, ultima_pagina, ultima_ejecucion, total_noticias FROM scraping_control")
    scraping_control = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    print("📊 ESTADÍSTICAS DEL SISTEMA")
    print("=" * 50)
    print(f"📰 Total de noticias: {total_news}")
    print()
    
    print("📋 Por fuente:")
    for fuente, count in by_source:
        print(f"   {fuente}: {count}")
    print()
    
    print("🕷️  Control de scraping:")
    for fuente, pagina, ejecucion, total in scraping_control:
        print(f"   {fuente}: Página {pagina}, Última ejecución: {ejecucion}, Total: {total}")
    print()
    
    print("📄 Últimas noticias:")
    for titulo, fuente, fecha in latest_news:
        print(f"   {titulo[:50]}... ({fuente}) - {fecha}")

if __name__ == "__main__":
    while True:
        get_stats()
        print("\n" + "="*50)
        time.sleep(60)  # Actualizar cada minuto
