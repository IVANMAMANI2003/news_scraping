#!/usr/bin/env python3
"""
Script para migrar datos de Puno Noticias desde CSV/JSON a PostgreSQL
"""

import glob
import json
import os
from datetime import datetime

import pandas as pd
import psycopg2


def connect_to_database():
    """Conectar a la base de datos PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="noticias",
            user="postgres",
            password="123456",
            port="5432"
        )
        print("✅ Conexión a PostgreSQL establecida")
        return conn
    except Exception as e:
        print(f"❌ Error al conectar con PostgreSQL: {e}")
        return None

def create_table_if_not_exists(conn):
    """Crear tabla si no existe"""
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
        
        cursor.execute(create_table_query)
        conn.commit()
        print("✅ Tabla 'noticias' verificada/creada")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al crear tabla: {e}")
        return False

def migrate_from_csv(csv_file, conn):
    """Migrar datos desde archivo CSV"""
    try:
        print(f"📄 Migrando desde CSV: {csv_file}")
        
        # Leer CSV
        df = pd.read_csv(csv_file)
        print(f"📊 Encontrados {len(df)} registros en CSV")
        
        cursor = conn.cursor()
        migrated_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            try:
                # Verificar si la URL ya existe
                cursor.execute("SELECT id FROM noticias WHERE url = %s", (row['url'],))
                if cursor.fetchone():
                    skipped_count += 1
                    continue
                
                # Insertar nuevo registro
                insert_query = """
                INSERT INTO noticias (
                    titulo, fecha, hora, resumen, contenido, categoria, autor, 
                    tags, url, fecha_extraccion, imagenes, fuente
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                    row.get('fuente', 'Puno Noticias')
                )
                
                cursor.execute(insert_query, values)
                migrated_count += 1
                
            except Exception as e:
                print(f"⚠️  Error en registro {index}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        
        print(f"✅ Migración CSV completada:")
        print(f"   - Migrados: {migrated_count}")
        print(f"   - Omitidos (duplicados): {skipped_count}")
        
        return migrated_count
        
    except Exception as e:
        print(f"❌ Error al migrar desde CSV: {e}")
        return 0

def migrate_from_json(json_file, conn):
    """Migrar datos desde archivo JSON"""
    try:
        print(f"📄 Migrando desde JSON: {json_file}")
        
        # Leer JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📊 Encontrados {len(data)} registros en JSON")
        
        cursor = conn.cursor()
        migrated_count = 0
        skipped_count = 0
        
        for item in data:
            try:
                # Verificar si la URL ya existe
                cursor.execute("SELECT id FROM noticias WHERE url = %s", (item['url'],))
                if cursor.fetchone():
                    skipped_count += 1
                    continue
                
                # Insertar nuevo registro
                insert_query = """
                INSERT INTO noticias (
                    titulo, fecha, hora, resumen, contenido, categoria, autor, 
                    tags, url, fecha_extraccion, imagenes, fuente
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                    item.get('fuente', 'Puno Noticias')
                )
                
                cursor.execute(insert_query, values)
                migrated_count += 1
                
            except Exception as e:
                print(f"⚠️  Error en registro: {e}")
                continue
        
        conn.commit()
        cursor.close()
        
        print(f"✅ Migración JSON completada:")
        print(f"   - Migrados: {migrated_count}")
        print(f"   - Omitidos (duplicados): {skipped_count}")
        
        return migrated_count
        
    except Exception as e:
        print(f"❌ Error al migrar desde JSON: {e}")
        return 0

def find_latest_files():
    """Encontrar los archivos más recientes de Puno Noticias"""
    data_folder = "data/punonoticias"
    
    if not os.path.exists(data_folder):
        print(f"❌ La carpeta {data_folder} no existe")
        return None, None
    
    # Buscar archivos CSV
    csv_files = glob.glob(f"{data_folder}/puno_noticias_*.csv")
    json_files = glob.glob(f"{data_folder}/puno_noticias_*.json")
    
    if not csv_files and not json_files:
        print(f"❌ No se encontraron archivos de Puno Noticias en {data_folder}")
        return None, None
    
    # Obtener el archivo más reciente
    latest_csv = max(csv_files, key=os.path.getctime) if csv_files else None
    latest_json = max(json_files, key=os.path.getctime) if json_files else None
    
    return latest_csv, latest_json

def show_database_stats(conn):
    """Mostrar estadísticas de la base de datos"""
    try:
        cursor = conn.cursor()
        
        # Contar total de registros
        cursor.execute("SELECT COUNT(*) FROM noticias;")
        total_count = cursor.fetchone()[0]
        
        # Contar por fuente
        cursor.execute("SELECT fuente, COUNT(*) FROM noticias GROUP BY fuente;")
        by_source = cursor.fetchall()
        
        # Últimos registros
        cursor.execute("SELECT titulo, fuente, created_at FROM noticias ORDER BY created_at DESC LIMIT 5;")
        latest = cursor.fetchall()
        
        print(f"\n📊 Estadísticas de la base de datos:")
        print(f"   - Total de noticias: {total_count}")
        print(f"   - Por fuente:")
        for fuente, count in by_source:
            print(f"     * {fuente}: {count}")
        
        print(f"   - Últimas 5 noticias:")
        for titulo, fuente, fecha in latest:
            print(f"     * {titulo[:50]}... ({fuente}) - {fecha}")
        
        cursor.close()
        
    except Exception as e:
        print(f"❌ Error al obtener estadísticas: {e}")

def main():
    """Función principal"""
    print("🔄 Migrador de Puno Noticias a PostgreSQL")
    print("=" * 50)
    
    # Conectar a la base de datos
    conn = connect_to_database()
    if not conn:
        return
    
    # Crear tabla si no existe
    if not create_table_if_not_exists(conn):
        return
    
    # Encontrar archivos más recientes
    csv_file, json_file = find_latest_files()
    
    if not csv_file and not json_file:
        print("❌ No se encontraron archivos para migrar")
        print("💡 Ejecuta primero: python spiders/punonoticias_local.py")
        return
    
    total_migrated = 0
    
    # Migrar desde CSV si existe
    if csv_file:
        migrated = migrate_from_csv(csv_file, conn)
        total_migrated += migrated
    
    # Migrar desde JSON si existe
    if json_file:
        migrated = migrate_from_json(json_file, conn)
        total_migrated += migrated
    
    # Mostrar estadísticas finales
    show_database_stats(conn)
    
    print(f"\n🎉 ¡Migración completada!")
    print(f"📊 Total de registros migrados: {total_migrated}")
    
    conn.close()

if __name__ == "__main__":
    main()
