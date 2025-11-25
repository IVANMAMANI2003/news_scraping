"""
Script para agregar relación (foreign key) entre noticias_limpia y noticias_bert_clean
"""

import os
import sys
from typing import Optional

import psycopg2

# Configuración de base de datos desde variables de entorno
DB_CONFIG = {
    'host': os.getenv('PGHOST', '127.0.0.1'),
    'port': os.getenv('PGPORT', '5432'),
    'database': os.getenv('PGDATABASE', 'noticias'),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', '123456')
}

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return None

def add_foreign_key_constraint(conn):
    """
    Agrega una foreign key constraint entre noticias_bert_clean.noticia_id y noticias_limpia.id
    También sincroniza los noticia_id basándose en la URL si es necesario
    """
    cursor = conn.cursor()
    
    try:
        print("🔗 Estableciendo relación entre noticias_limpia y noticias_bert_clean...")
        
        # Paso 1: Sincronizar noticia_id basándose en URL si noticia_id es NULL
        print("\n📋 Paso 1: Sincronizando noticia_id basándose en URL...")
        sync_query = """
            UPDATE noticias_bert_clean nbc
            SET noticia_id = nl.id
            FROM noticias_limpia nl
            WHERE nbc.url = nl.url
            AND nbc.noticia_id IS NULL
            AND nl.url IS NOT NULL;
        """
        cursor.execute(sync_query)
        synced_count = cursor.rowcount
        conn.commit()
        print(f"✅ {synced_count} registros sincronizados")
        
        # Paso 2: Verificar que hay registros con noticia_id válido
        cursor.execute("""
            SELECT COUNT(*) 
            FROM noticias_bert_clean 
            WHERE noticia_id IS NOT NULL
        """)
        valid_count = cursor.fetchone()[0]
        print(f"📊 Registros con noticia_id válido: {valid_count}")
        
        if valid_count == 0:
            print("⚠️ No hay registros con noticia_id válido. No se puede crear la foreign key.")
            return False
        
        # Paso 3: Eliminar registros huérfanos (sin correspondencia en noticias_limpia)
        print("\n🧹 Paso 2: Eliminando registros huérfanos...")
        delete_orphans_query = """
            DELETE FROM noticias_bert_clean
            WHERE noticia_id IS NOT NULL
            AND noticia_id NOT IN (SELECT id FROM noticias_limpia);
        """
        cursor.execute(delete_orphans_query)
        deleted_count = cursor.rowcount
        conn.commit()
        if deleted_count > 0:
            print(f"✅ {deleted_count} registros huérfanos eliminados")
        else:
            print("✅ No hay registros huérfanos")
        
        # Paso 4: Agregar foreign key constraint
        print("\n🔗 Paso 3: Agregando foreign key constraint...")
        
        # Primero eliminar constraint si existe
        drop_fk_query = """
            ALTER TABLE noticias_bert_clean 
            DROP CONSTRAINT IF EXISTS fk_noticia_limpia;
        """
        cursor.execute(drop_fk_query)
        conn.commit()
        
        # Crear la foreign key constraint
        create_fk_query = """
            ALTER TABLE noticias_bert_clean
            ADD CONSTRAINT fk_noticia_limpia
            FOREIGN KEY (noticia_id)
            REFERENCES noticias_limpia(id)
            ON DELETE CASCADE
            ON UPDATE CASCADE;
        """
        
        cursor.execute(create_fk_query)
        conn.commit()
        print("✅ Foreign key constraint creada exitosamente")
        
        # Paso 5: Crear índice adicional para mejorar rendimiento
        print("\n📊 Paso 4: Creando índices adicionales...")
        create_index_query = """
            CREATE INDEX IF NOT EXISTS idx_bert_clean_noticia_id_fk 
            ON noticias_bert_clean(noticia_id);
        """
        cursor.execute(create_index_query)
        conn.commit()
        print("✅ Índice creado")
        
        # Paso 6: Estadísticas finales
        print("\n📈 Paso 5: Estadísticas finales...")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_bert,
                COUNT(noticia_id) as con_relacion,
                COUNT(*) - COUNT(noticia_id) as sin_relacion
            FROM noticias_bert_clean
        """)
        stats = cursor.fetchone()
        print(f"📊 Total registros en noticias_bert_clean: {stats[0]}")
        print(f"📊 Con relación (noticia_id): {stats[1]}")
        print(f"📊 Sin relación (noticia_id NULL): {stats[2]}")
        
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        return False
    finally:
        cursor.close()

def main():
    """Función principal"""
    print("=" * 60)
    print("🔗 ESTABLECIENDO RELACIÓN ENTRE TABLAS")
    print("=" * 60)
    print(f"📊 Base de datos: {DB_CONFIG['database']}")
    print(f"📊 Host: {DB_CONFIG['host']}")
    print("=" * 60)
    
    conn = get_db_connection()
    if not conn:
        sys.exit(1)
    
    try:
        success = add_foreign_key_constraint(conn)
        if success:
            print("\n" + "=" * 60)
            print("✅ RELACIÓN ESTABLECIDA EXITOSAMENTE")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠️ NO SE PUDO ESTABLECER LA RELACIÓN")
            print("=" * 60)
            sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()

