#!/usr/bin/env python3
"""
Script para configurar la base de datos PostgreSQL para el proyecto de scraping
"""

import sys

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def verify_database():
    """Verifica que la base de datos 'noticias' existe y es accesible"""
    try:
        # Conectar directamente a la base de datos 'noticias'
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="noticias",
            user="postgres",
            password="123456",
            port="5432"
        )
        cursor = conn.cursor()
        
        # Verificar conexión
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conexión exitosa a la base de datos 'noticias'")
        print(f"📊 Versión de PostgreSQL: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos 'noticias': {e}")
        print("💡 Verifica que:")
        print("   - PostgreSQL esté ejecutándose")
        print("   - La base de datos 'noticias' exista")
        print("   - Las credenciales sean correctas")
        return False

def create_table():
    """Crea la tabla de noticias"""
    try:
        # Conectar a la base de datos 'noticias'
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="noticias",
            user="postgres",
            password="123456",  # Cambia por tu contraseña
            port="5432"
        )
        cursor = conn.cursor()
        
        # Crear tabla de noticias
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
        
        print("✅ Tabla 'noticias' creada correctamente")
        
        # Crear índices para mejorar el rendimiento
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_noticias_url ON noticias(url);",
            "CREATE INDEX IF NOT EXISTS idx_noticias_fecha ON noticias(fecha);",
            "CREATE INDEX IF NOT EXISTS idx_noticias_fuente ON noticias(fuente);",
            "CREATE INDEX IF NOT EXISTS idx_noticias_categoria ON noticias(categoria);"
        ]
        
        for index_query in indexes:
            cursor.execute(index_query)
        
        conn.commit()
        print("✅ Índices creados correctamente")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error al crear la tabla: {e}")
        sys.exit(1)

def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="noticias",
            user="postgres",
            password="123456",  # Cambia por tu contraseña
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conexión exitosa a PostgreSQL: {version[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Configurando base de datos PostgreSQL...")
    print("=" * 50)
    
    print("\n1. Verificando conexión a la base de datos...")
    if not verify_database():
        print("❌ No se pudo conectar a la base de datos 'noticias'")
        print("💡 Asegúrate de que:")
        print("   - PostgreSQL esté ejecutándose")
        print("   - La base de datos 'noticias' exista")
        print("   - Las credenciales sean correctas")
        sys.exit(1)

    print("\n2. Creando tabla de noticias...")
    create_table()

    print("\n3. Probando conexión final...")
    test_connection()
    
    print("\n" + "=" * 50)
    print("✅ ¡Configuración completada!")
    print("\n📝 Próximos pasos:")
    print("1. Asegúrate de que PostgreSQL esté ejecutándose")
    print("2. Modifica la contraseña en el archivo .env si es necesario")
    print("3. Ejecuta los spiders con: scrapy crawl <nombre_spider>")
    print("4. Los datos se guardarán automáticamente en PostgreSQL")
