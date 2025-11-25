"""
Script para limpiar tablas de la base de datos
"""
import argparse
import logging
import os
import sys

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Obtiene conexión a la base de datos.
    
    Returns:
        Conexión a PostgreSQL
    """
    try:
        # Intentar usar variables de entorno o valores por defecto
        host = os.getenv("PGHOST", "127.0.0.1")
        port = os.getenv("PGPORT", "5432")
        database = os.getenv("PGDATABASE", "noticias")
        user = os.getenv("PGUSER", "postgres")
        password = os.getenv("PGPASSWORD", "123456")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        logger.info("✅ Conexión a base de datos establecida")
        return conn
    except psycopg2.Error as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        return None


def limpiar_tabla(conn, tabla: str = "noticias_limpia", no_confirmar: bool = False):
    """
    Limpia (trunca) una tabla.
    
    Args:
        conn: Conexión a la base de datos
        tabla: Nombre de la tabla a limpiar
        no_confirmar: Si es True, no pide confirmación
    """
    cursor = conn.cursor()
    
    try:
        # Verificar que la tabla existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (tabla,))
        
        existe = cursor.fetchone()[0]
        
        if not existe:
            logger.error(f"❌ La tabla '{tabla}' no existe")
            return False
        
        # Contar registros antes de limpiar
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        count_antes = cursor.fetchone()[0]
        
        logger.info(f"📊 Registros en '{tabla}' antes de limpiar: {count_antes}")
        
        # Confirmar acción (a menos que se especifique --no-confirmar)
        if not no_confirmar:
            respuesta = input(f"\n⚠️  ¿Estás seguro de que quieres limpiar la tabla '{tabla}'? (sí/no): ")
            
            if respuesta.lower() not in ['sí', 'si', 'yes', 'y', 's']:
                logger.info("❌ Operación cancelada")
                return False
        
        # Truncar la tabla
        cursor.execute(f"TRUNCATE TABLE {tabla} RESTART IDENTITY CASCADE")
        conn.commit()
        
        logger.info(f"✅ Tabla '{tabla}' limpiada exitosamente")
        logger.info(f"   Se eliminaron {count_antes} registros")
        
        return True
        
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"❌ Error limpiando la tabla: {e}")
        return False
    finally:
        cursor.close()


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Limpiar una tabla de la base de datos")
    parser.add_argument(
        "--tabla",
        type=str,
        default="noticias",
        help="Nombre de la tabla a limpiar (default: noticias)"
    )
    parser.add_argument(
        "--no-confirmar",
        action="store_true",
        help="No pedir confirmación (útil para scripts)"
    )
    
    args = parser.parse_args()
    tabla = args.tabla
    
    print("=" * 70)
    print(f"LIMPIEZA DE TABLA - {tabla}")
    print("=" * 70)
    print()
    
    # Conectar a la base de datos
    conn = get_db_connection()
    if not conn:
        sys.exit(1)
    
    try:
        # Limpiar la tabla
        exito = limpiar_tabla(conn, tabla, no_confirmar=args.no_confirmar)
        
        if exito:
            print()
            print("=" * 70)
            print("✅ OPERACIÓN COMPLETADA")
            print("=" * 70)
        else:
            print()
            print("=" * 70)
            print("❌ OPERACIÓN FALLIDA")
            print("=" * 70)
            sys.exit(1)
            
    finally:
        conn.close()
        logger.info("🔌 Conexión cerrada")


if __name__ == "__main__":
    main()

