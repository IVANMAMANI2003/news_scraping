"""
Script de integración para procesar noticias con Ollama y guardar en base de datos.

Este script:
1. Lee noticias de la tabla 'noticias' o 'noticias_limpia'
2. Procesa cada noticia usando Ollama (deepseek-r1:8b)
3. Guarda el contenido limpio en una nueva tabla 'noticias_bert_clean'
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm

# Importar desde el mismo directorio
try:
    from nlp_cleaner import NLPContentCleaner, clean_news
except ImportError:
    # Si se ejecuta desde otro directorio
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from nlp_cleaning.nlp_cleaner import NLPContentCleaner, clean_news

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


def create_bert_clean_table(conn):
    """
    Crea la tabla 'noticias_bert_clean' para almacenar contenido limpio.
    
    Args:
        conn: Conexión a la base de datos
    
    Returns:
        True si se creó exitosamente, False en caso contrario
    """
    cursor = conn.cursor()
    
    # Primero crear la tabla si no existe
    create_table_query = """
    CREATE TABLE IF NOT EXISTS noticias_bert_clean (
        id SERIAL PRIMARY KEY,
        noticia_id INTEGER,
        titulo TEXT NOT NULL,
        resumen TEXT,
        contenido_raw TEXT,
        contenido_limpio TEXT,
        parrafos_relevantes JSONB,
        parrafos_irrelevantes JSONB,
        num_parrafos_total INTEGER,
        num_parrafos_relevantes INTEGER,
        num_parrafos_irrelevantes INTEGER,
        procesado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        url TEXT,
        fuente VARCHAR(100),
        fecha TIMESTAMP,
        modelo_usado VARCHAR(50) DEFAULT 'deepseek-r1:8b'
    );
    """
    
    # Luego agregar las columnas que puedan faltar (para tablas existentes)
    alter_table_queries = [
        "ALTER TABLE noticias_bert_clean ADD COLUMN IF NOT EXISTS parrafos_relevantes JSONB;",
        "ALTER TABLE noticias_bert_clean ADD COLUMN IF NOT EXISTS parrafos_irrelevantes JSONB;",
        "ALTER TABLE noticias_bert_clean ADD COLUMN IF NOT EXISTS num_parrafos_total INTEGER;",
        "ALTER TABLE noticias_bert_clean ADD COLUMN IF NOT EXISTS num_parrafos_relevantes INTEGER;",
        "ALTER TABLE noticias_bert_clean ADD COLUMN IF NOT EXISTS num_parrafos_irrelevantes INTEGER;",
        "ALTER TABLE noticias_bert_clean ADD COLUMN IF NOT EXISTS modelo_usado VARCHAR(50) DEFAULT 'deepseek-r1:8b';",
    ]
    
    # Eliminar foreign key constraint antigua si existe (para recrearla correctamente)
    drop_fk_queries = [
        "ALTER TABLE noticias_bert_clean DROP CONSTRAINT IF EXISTS fk_noticia;",
        "ALTER TABLE noticias_bert_clean DROP CONSTRAINT IF EXISTS fk_noticia_limpia;",
    ]
    
    # Crear índice único en url si no existe (para ON CONFLICT)
    create_unique_queries = [
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_noticias_bert_clean_url ON noticias_bert_clean(url) WHERE url IS NOT NULL;",
    ]
    
    # Índices
    create_index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_bert_clean_noticia_id ON noticias_bert_clean(noticia_id);",
        "CREATE INDEX IF NOT EXISTS idx_bert_clean_url ON noticias_bert_clean(url);",
        "CREATE INDEX IF NOT EXISTS idx_bert_clean_fuente ON noticias_bert_clean(fuente);",
        "CREATE INDEX IF NOT EXISTS idx_bert_clean_procesado_at ON noticias_bert_clean(procesado_at);",
    ]
    
    try:
        # Crear tabla
        cursor.execute(create_table_query)
        conn.commit()
        
        # Eliminar foreign key constraint si existe (para permitir noticias de diferentes tablas)
        for drop_fk_query in drop_fk_queries:
            try:
                cursor.execute(drop_fk_query)
                conn.commit()
            except psycopg2.Error as e:
                conn.rollback()
        
        # Crear constraint UNIQUE en url si no existe
        for unique_query in create_unique_queries:
            try:
                cursor.execute(unique_query)
                conn.commit()
            except psycopg2.Error as e:
                conn.rollback()
        
        # Agregar columnas que puedan faltar
        for alter_query in alter_table_queries:
            try:
                cursor.execute(alter_query)
                conn.commit()
            except psycopg2.Error as e:
                # Ignorar errores si la columna ya existe
                conn.rollback()
        
        # Crear índices
        for index_query in create_index_queries:
            try:
                cursor.execute(index_query)
                conn.commit()
            except psycopg2.Error as e:
                conn.rollback()
        
        # Sincronizar noticia_id basándose en URL si es necesario
        try:
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
            if synced_count > 0:
                conn.commit()
                logger.info(f"✅ {synced_count} registros sincronizados con noticia_id")
        except psycopg2.Error as e:
            conn.rollback()
            logger.warning(f"⚠️ No se pudieron sincronizar noticia_id: {e}")
        
        # Intentar crear foreign key constraint (solo si hay registros con noticia_id válido)
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM noticias_bert_clean 
                WHERE noticia_id IS NOT NULL
            """)
            valid_count = cursor.fetchone()[0]
            
            if valid_count > 0:
                # Eliminar registros huérfanos antes de crear la FK
                cursor.execute("""
                    DELETE FROM noticias_bert_clean
                    WHERE noticia_id IS NOT NULL
                    AND noticia_id NOT IN (SELECT id FROM noticias_limpia);
                """)
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    conn.commit()
                    logger.info(f"✅ {deleted_count} registros huérfanos eliminados")
                
                # Crear foreign key constraint
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
                logger.info("✅ Foreign key constraint creada exitosamente")
            else:
                logger.warning("⚠️ No hay registros con noticia_id válido. No se creó la foreign key.")
        except psycopg2.Error as e:
            conn.rollback()
            # Si la constraint ya existe, no es un error crítico
            if "already exists" not in str(e).lower():
                logger.warning(f"⚠️ No se pudo crear foreign key constraint: {e}")
        
        logger.info("✅ Tabla 'noticias_bert_clean' creada/verificada exitosamente")
        return True
    except psycopg2.Error as e:
        logger.error(f"❌ Error creando tabla: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()


def get_news_to_process(conn, source_table: str = "noticias", limit: Optional[int] = None):
    """
    Obtiene noticias para procesar.
    
    Args:
        conn: Conexión a la base de datos
        source_table: Tabla de origen ('noticias' o 'noticias_limpia')
        limit: Límite de noticias a procesar (None para todas)
    
    Returns:
        Lista de tuplas con (id, titulo, resumen, contenido, url, fuente, fecha)
    """
    cursor = conn.cursor()
    
    # Verificar si la tabla existe
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (source_table,))
    
    if not cursor.fetchone()[0]:
        logger.error(f"❌ La tabla '{source_table}' no existe")
        cursor.close()
        return []
    
    # Construir query
    query = f"""
        SELECT id, titulo, resumen, contenido, url, fuente, fecha
        FROM {source_table}
        WHERE contenido IS NOT NULL 
        AND contenido != ''
        AND titulo IS NOT NULL
        AND titulo != ''
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        logger.info(f"📊 Encontradas {len(results)} noticias para procesar")
        return results
    except psycopg2.Error as e:
        logger.error(f"❌ Error obteniendo noticias: {e}")
        return []
    finally:
        cursor.close()


def get_already_processed_urls(conn) -> set:
    """
    Obtiene las URLs ya procesadas para evitar duplicados.
    
    Args:
        conn: Conexión a la base de datos
    
    Returns:
        Set de URLs ya procesadas
    """
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT DISTINCT url FROM noticias_bert_clean WHERE url IS NOT NULL")
        urls = {row[0] for row in cursor.fetchall()}
        logger.info(f"📊 {len(urls)} noticias ya procesadas")
        return urls
    except psycopg2.Error as e:
        logger.warning(f"⚠️ Error obteniendo URLs procesadas: {e}")
        return set()
    finally:
        cursor.close()


def process_news_batch(
    conn,
    news_batch: List[tuple],
    model_name: str = "deepseek-r1:8b",
    ollama_base_url: Optional[str] = None
):
    """
    Procesa un lote de noticias usando Ollama.
    
    Args:
        conn: Conexión a la base de datos
        news_batch: Lista de tuplas (id, titulo, resumen, contenido, url, fuente, fecha)
        model_name: Nombre del modelo de Ollama
        ollama_base_url: URL base de Ollama
    
    Returns:
        Tupla (procesadas, errores)
    """
    cursor = conn.cursor()
    processed = 0
    errors = 0
    
    # Verificar si la URL existe antes de insertar
    check_url_query = "SELECT id FROM noticias_bert_clean WHERE url = %s"
    
    insert_query = """
        INSERT INTO noticias_bert_clean (
            noticia_id, titulo, resumen, contenido_raw, contenido_limpio,
            parrafos_relevantes, parrafos_irrelevantes,
            num_parrafos_total, num_parrafos_relevantes, num_parrafos_irrelevantes,
            url, fuente, fecha, modelo_usado
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    
    update_query = """
        UPDATE noticias_bert_clean SET
            contenido_limpio = %s,
            parrafos_relevantes = %s,
            parrafos_irrelevantes = %s,
            num_parrafos_total = %s,
            num_parrafos_relevantes = %s,
            num_parrafos_irrelevantes = %s,
            procesado_at = CURRENT_TIMESTAMP
        WHERE url = %s
    """
    
    batch_data = []
    
    for news_item in tqdm(news_batch, desc="Procesando noticias"):
        noticia_id, titulo, resumen, contenido, url, fuente, fecha = news_item
        
        try:
            # Limpiar noticia usando Ollama
            result = clean_news(
                title=titulo or "",
                summary=resumen or "",
                raw=contenido or "",
                model_name=model_name,
                ollama_base_url=ollama_base_url
            )
            
            # Calcular métricas (ahora son oraciones, no párrafos)
            num_oraciones_relevantes = len(result.get('relevantes', []))
            num_oraciones_irrelevantes = len(result.get('irrelevantes', []))
            num_oraciones_total = num_oraciones_relevantes + num_oraciones_irrelevantes
            
            # Para compatibilidad con BD, mantener nombres de columnas pero son oraciones
            num_parrafos_relevantes = num_oraciones_relevantes
            num_parrafos_irrelevantes = num_oraciones_irrelevantes
            num_parrafos_total = num_oraciones_total
            
            # Convertir listas a JSON
            parrafos_relevantes_json = json.dumps(result.get('relevantes', []), ensure_ascii=False)
            parrafos_irrelevantes_json = json.dumps(result.get('irrelevantes', []), ensure_ascii=False)
            
            # Si noticia_id es NULL, intentar obtenerlo de noticias_limpia basándose en URL
            final_noticia_id = noticia_id
            if not final_noticia_id and url:
                try:
                    cursor.execute("""
                        SELECT id FROM noticias_limpia WHERE url = %s LIMIT 1
                    """, (url,))
                    result_id = cursor.fetchone()
                    if result_id:
                        final_noticia_id = result_id[0]
                except psycopg2.Error:
                    pass  # Si falla, usar NULL
            
            # Preparar datos para inserción
            batch_data.append((
                final_noticia_id,
                titulo,
                resumen,
                contenido,
                result.get('clean_text', ''),
                parrafos_relevantes_json,
                parrafos_irrelevantes_json,
                num_parrafos_total,
                num_parrafos_relevantes,
                num_parrafos_irrelevantes,
                url,
                fuente,
                fecha,
                model_name
            ))
            
            processed += 1
            
        except Exception as e:
            logger.error(f"❌ Error procesando noticia ID {noticia_id}: {e}")
            errors += 1
            continue
    
    # Insertar o actualizar en lote
    if batch_data:
        try:
            inserted = 0
            updated = 0
            
            for row in batch_data:
                noticia_id, titulo, resumen, contenido, clean_text, parrafos_relevantes_json, \
                parrafos_irrelevantes_json, num_parrafos_total, num_parrafos_relevantes, \
                num_parrafos_irrelevantes, url, fuente, fecha, model_name = row
                
                # Verificar si existe
                cursor.execute(check_url_query, (url,))
                exists = cursor.fetchone()
                
                if exists:
                    # Actualizar
                    cursor.execute(update_query, (
                        clean_text, parrafos_relevantes_json, parrafos_irrelevantes_json,
                        num_parrafos_total, num_parrafos_relevantes, num_parrafos_irrelevantes,
                        url
                    ))
                    updated += 1
                else:
                    # Insertar
                    cursor.execute(insert_query, row)
                    inserted += 1
            
            conn.commit()
            logger.info(f"✅ Procesadas {len(batch_data)} noticias: {inserted} insertadas, {updated} actualizadas")
        except Exception as e:
            logger.error(f"❌ Error insertando/actualizando datos: {e}")
            conn.rollback()
            processed = 0
    
    cursor.close()
    return processed, errors


def process_all_news(
    source_table: str = "noticias_limpia",  # Por defecto leer de 'noticias_limpia'
    batch_size: int = 10,
    limit: Optional[int] = None,
    model_name: str = "deepseek-r1:8b",
    ollama_base_url: Optional[str] = None,
    skip_processed: bool = True
):
    """
    Procesa todas las noticias de la base de datos.
    
    Args:
        source_table: Tabla de origen ('noticias' o 'noticias_limpia')
        batch_size: Tamaño del lote para procesamiento
        limit: Límite de noticias a procesar (None para todas)
        model_name: Nombre del modelo de Ollama
        ollama_base_url: URL base de Ollama
        skip_processed: Si True, omite noticias ya procesadas
    """
    # Conectar a la base de datos
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        # Crear tabla si no existe
        if not create_bert_clean_table(conn):
            return False
        
        # Obtener noticias para procesar
        all_news = get_news_to_process(conn, source_table=source_table, limit=limit)
        
        if not all_news:
            logger.warning("⚠️ No se encontraron noticias para procesar")
            return False
        
        # Filtrar ya procesadas si es necesario
        if skip_processed:
            processed_urls = get_already_processed_urls(conn)
            all_news = [n for n in all_news if n[4] not in processed_urls]  # n[4] es url
            logger.info(f"📊 {len(all_news)} noticias nuevas para procesar")
        
        if not all_news:
            logger.info("✅ Todas las noticias ya han sido procesadas")
            return True
        
        # Procesar en lotes
        total_processed = 0
        total_errors = 0
        
        for i in range(0, len(all_news), batch_size):
            batch = all_news[i:i + batch_size]
            logger.info(f"\n{'='*60}")
            logger.info(f"Procesando lote {i//batch_size + 1}/{(len(all_news) + batch_size - 1)//batch_size}")
            logger.info(f"{'='*60}")
            
            processed, errors = process_news_batch(
                conn,
                batch,
                model_name=model_name,
                ollama_base_url=ollama_base_url
            )
            
            total_processed += processed
            total_errors += errors
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ Procesamiento completado")
        logger.info(f"   📊 Total procesadas: {total_processed}")
        logger.info(f"   ❌ Total errores: {total_errors}")
        logger.info(f"{'='*60}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en el proceso: {e}")
        return False
    finally:
        conn.close()


def main():
    """Función principal para ejecutar desde línea de comandos."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Procesar noticias con Ollama y guardar contenido limpio'
    )
    parser.add_argument(
        '--source-table',
        type=str,
        default='noticias_limpia',  # Por defecto leer de 'noticias_limpia'
        choices=['noticias', 'noticias_limpia'],
        help='Tabla de origen de las noticias (default: noticias_limpia)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Tamaño del lote para procesamiento (default: 10, recomendado para Ollama)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Límite de noticias a procesar (None para todas)'
    )
    parser.add_argument(
        '--model-name',
        type=str,
        default='deepseek-r1:8b',
        help='Nombre del modelo de Ollama'
    )
    parser.add_argument(
        '--ollama-url',
        type=str,
        default=None,
        help='URL base de Ollama (default: http://localhost:11434)'
    )
    parser.add_argument(
        '--no-skip-processed',
        action='store_true',
        help='No omitir noticias ya procesadas'
    )
    
    args = parser.parse_args()
    
    success = process_all_news(
        source_table=args.source_table,
        batch_size=args.batch_size,
        limit=args.limit,
        model_name=args.model_name,
        ollama_base_url=args.ollama_url,
        skip_processed=not args.no_skip_processed
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
