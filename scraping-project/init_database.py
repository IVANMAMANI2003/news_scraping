#!/usr/bin/env python3
"""
Script para inicializar la base de datos PostgreSQL
"""

import os
import time

import psycopg2


def wait_for_postgres(host, port, user, password, database, max_retries=30):
    """Esperar a que PostgreSQL esté listo"""
    print("🔄 Esperando que PostgreSQL esté listo...")
    
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            conn.close()
            print("✅ PostgreSQL conectado")
            return True
        except psycopg2.OperationalError:
            print(f"⏳ Intento {i+1}/{max_retries} - Esperando PostgreSQL...")
            time.sleep(2)
    
    print("❌ No se pudo conectar a PostgreSQL")
    return False

def create_database_and_table():
    """Crear base de datos y tabla si no existen"""
    
    # Configuración de conexión
    host = os.getenv('POSTGRES_HOST', 'news_postgres_prod')
    port = os.getenv('POSTGRES_PORT', '5432')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', '123456')
    database = os.getenv('POSTGRES_DB', 'noticias')
    
    print("🐘 INICIALIZANDO BASE DE DATOS POSTGRESQL")
    print("=" * 60)
    print(f"Host: {host}")
    print(f"Puerto: {port}")
    print(f"Usuario: {user}")
    print(f"Base de datos: {database}")
    print("=" * 60)
    
    # Esperar a que PostgreSQL esté listo
    if not wait_for_postgres(host, port, user, password, 'postgres'):
        return False
    
    try:
        # Conectar a la base de datos postgres (por defecto)
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Crear base de datos si no existe
        print("📊 Creando base de datos...")
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{database}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {database}")
            print(f"✅ Base de datos '{database}' creada")
        else:
            print(f"✅ Base de datos '{database}' ya existe")
        
        cursor.close()
        conn.close()
        
        # Conectar a la base de datos específica
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Crear tabla noticias
        print("📋 Creando tabla noticias...")
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
        
        # Verificar que la tabla existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'noticias'
        """)
        
        if cursor.fetchone()[0] > 0:
            print("✅ Tabla 'noticias' verificada")
            
            # Mostrar estructura de la tabla
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'noticias'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            print("\n📋 Estructura de la tabla:")
            for col_name, data_type, nullable in columns:
                print(f"   {col_name}: {data_type} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
        else:
            print("❌ Error: No se pudo crear la tabla")
            return False
        
        cursor.close()
        conn.close()
        
        print("\n🎉 ¡Base de datos inicializada correctamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_database_and_table()
    if success:
        print("\n✅ ¡Inicialización completada!")
    else:
        print("\n❌ Error en la inicialización")
        exit(1)
