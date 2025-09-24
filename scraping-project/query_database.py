#!/usr/bin/env python3
"""
Script para consultar la base de datos PostgreSQL en Docker
"""

import psycopg2

from config.database import get_db_connection


def show_database_stats():
    """Mostrar estadísticas de la base de datos"""
    print("📊 ESTADÍSTICAS DE LA BASE DE DATOS")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total de noticias
        cursor.execute("SELECT COUNT(*) FROM noticias")
        total = cursor.fetchone()[0]
        print(f"📰 Total de noticias: {total}")
        
        # Noticias por fuente
        print(f"\n📈 Noticias por fuente:")
        cursor.execute("SELECT fuente, COUNT(*) as total FROM noticias GROUP BY fuente ORDER BY total DESC")
        sources = cursor.fetchall()
        for fuente, count in sources:
            print(f"   {fuente}: {count} noticias")
        
        # Últimas noticias
        print(f"\n🕒 Últimas 5 noticias:")
        cursor.execute("""
            SELECT titulo, fuente, fecha_extraccion 
            FROM noticias 
            ORDER BY fecha_extraccion DESC 
            LIMIT 5
        """)
        latest = cursor.fetchall()
        for titulo, fuente, fecha in latest:
            print(f"   📄 {titulo[:50]}... ({fuente}) - {fecha}")
        
        # Noticias de hoy
        cursor.execute("""
            SELECT COUNT(*) FROM noticias 
            WHERE DATE(fecha_extraccion) = CURRENT_DATE
        """)
        today = cursor.fetchone()[0]
        print(f"\n📅 Noticias de hoy: {today}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def search_news(keyword):
    """Buscar noticias por palabra clave"""
    print(f"🔍 Buscando noticias con '{keyword}'...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT titulo, fuente, fecha_extraccion 
            FROM noticias 
            WHERE titulo ILIKE %s OR contenido ILIKE %s
            ORDER BY fecha_extraccion DESC 
            LIMIT 10
        """, (f'%{keyword}%', f'%{keyword}%'))
        
        results = cursor.fetchall()
        
        if results:
            print(f"✅ Encontradas {len(results)} noticias:")
            for titulo, fuente, fecha in results:
                print(f"   📄 {titulo[:60]}... ({fuente}) - {fecha}")
        else:
            print("❌ No se encontraron noticias")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_table_structure():
    """Mostrar estructura de la tabla"""
    print("🏗️  ESTRUCTURA DE LA TABLA 'noticias'")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'noticias'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        print("Columnas de la tabla:")
        for col_name, data_type, nullable, default in columns:
            print(f"   {col_name}: {data_type} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
            if default:
                print(f"      Default: {default}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("🐘 CONSULTOR DE BASE DE DATOS POSTGRESQL")
    print("=" * 60)
    
    while True:
        print("\n¿Qué quieres hacer?")
        print("1. Ver estadísticas generales")
        print("2. Buscar noticias por palabra clave")
        print("3. Ver estructura de la tabla")
        print("4. Salir")
        
        choice = input("\nOpción (1-4): ").strip()
        
        if choice == '1':
            show_database_stats()
        
        elif choice == '2':
            keyword = input("Palabra clave a buscar: ").strip()
            if keyword:
                search_news(keyword)
            else:
                print("❌ Palabra clave vacía")
        
        elif choice == '3':
            show_table_structure()
        
        elif choice == '4':
            print("👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()
