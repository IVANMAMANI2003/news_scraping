"""
Script para restaurar datos del backup SQL a la base de datos local.
Solo inserta datos en las tablas noticias y social_news, evitando duplicados.
"""
import os
import subprocess
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

# Ruta al archivo de backup
BACKUP_FILE = Path(__file__).resolve().parent / "backup.sql"

# Configuración de la base de datos local
DB_CONFIG = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": os.getenv("PGPORT", "5432"),
    "database": os.getenv("PGDATABASE", "noticias"),
    "user": os.getenv("PGUSER", "postgres"),
    "password": os.getenv("PGPASSWORD", "123456"),
}


def check_backup_file():
    """Verifica que el archivo de backup exista"""
    if not BACKUP_FILE.exists():
        print(f"❌ Error: No se encontró el archivo de backup en: {BACKUP_FILE}")
        return False
    print(f"✅ Archivo de backup encontrado: {BACKUP_FILE}")
    print(f"   Tamaño: {BACKUP_FILE.stat().st_size / (1024*1024):.2f} MB")
    return True


def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Conexión exitosa a PostgreSQL: {version.split(',')[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        print(f"   Configuración: host={DB_CONFIG['host']}, db={DB_CONFIG['database']}, user={DB_CONFIG['user']}")
        return False


def check_tables_exist():
    """Verifica que las tablas noticias y social_news existan"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'noticias'
            );
        """)
        noticias_exists = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'social_news'
            );
        """)
        social_news_exists = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        if not noticias_exists:
            print("❌ Error: La tabla 'noticias' no existe en la base de datos")
            return False
        if not social_news_exists:
            print("⚠️  Advertencia: La tabla 'social_news' no existe. Se creará automáticamente si hay datos.")
        
        print("✅ Tablas verificadas correctamente")
        return True
    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")
        return False


def find_psql():
    """Busca psql en ubicaciones comunes"""
    import shutil

    # Primero intentar encontrar en PATH
    psql_path = shutil.which("psql")
    if psql_path:
        return psql_path
    
    # Buscar en ubicaciones comunes de Windows
    common_paths = [
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\13\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\15\bin\psql.exe",
        r"C:\Program Files (x86)\PostgreSQL\14\bin\psql.exe",
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None


def extract_and_process_data():
    """Extrae y procesa los datos del backup, removiendo el campo id para generar IDs incrementales"""
    print("\n📝 Extrayendo y procesando datos de noticias y social_news del backup...")
    
    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar las secciones COPY
    lines = content.split('\n')
    noticias_data = []
    social_news_data = []
    
    in_noticias_copy = False
    in_social_copy = False
    noticias_columns = None
    social_columns = None
    
    for i, line in enumerate(lines):
        # Detectar inicio de COPY para noticias
        if 'COPY public.noticias' in line or ('COPY noticias' in line and '(' in line):
            in_noticias_copy = True
            in_social_copy = False
            # Extraer nombres de columnas
            if '(' in line and ')' in line:
                cols_part = line[line.find('(')+1:line.find(')')]
                noticias_columns = [col.strip() for col in cols_part.split(',')]
                print(f"   📋 Columnas de noticias: {len(noticias_columns)} columnas")
                # Remover 'id' de las columnas
                if 'id' in noticias_columns:
                    noticias_columns.remove('id')
                    print(f"   ✅ Campo 'id' excluido - se generarán IDs automáticamente")
            continue
        # Detectar inicio de COPY para social_news
        elif 'COPY public.social_news' in line or ('COPY social_news' in line and '(' in line):
            in_noticias_copy = False
            in_social_copy = True
            # Extraer nombres de columnas
            if '(' in line and ')' in line:
                cols_part = line[line.find('(')+1:line.find(')')]
                social_columns = [col.strip() for col in cols_part.split(',')]
                print(f"   📋 Columnas de social_news: {len(social_columns)} columnas")
                # Remover 'id' de las columnas
                if 'id' in social_columns:
                    social_columns.remove('id')
                    print(f"   ✅ Campo 'id' excluido - se generarán IDs automáticamente")
            continue
        # Detectar fin de COPY
        elif line.strip() == '\\.' or line.strip() == '.':
            if in_noticias_copy or in_social_copy:
                in_noticias_copy = False
                in_social_copy = False
            continue
        # Procesar líneas de datos
        elif in_noticias_copy and line.strip():
            # Remover el primer campo (id) de la línea
            parts = line.split('\t')
            expected_cols = len(noticias_columns) if noticias_columns else 0
            # Si removemos id, deberíamos tener expected_cols campos
            if len(parts) > 1:
                # Remover el primer campo (id) y unir el resto
                data_without_id = '\t'.join(parts[1:])
                # Validar que tengamos el número correcto de campos
                remaining_parts = parts[1:]
                if expected_cols > 0 and len(remaining_parts) != expected_cols:
                    # Ajustar: si faltan campos, agregar NULLs; si sobran, truncar
                    if len(remaining_parts) < expected_cols:
                        remaining_parts.extend(['\\N'] * (expected_cols - len(remaining_parts)))
                    elif len(remaining_parts) > expected_cols:
                        remaining_parts = remaining_parts[:expected_cols]
                    data_without_id = '\t'.join(remaining_parts)
                noticias_data.append(data_without_id)
        elif in_social_copy and line.strip():
            # Remover el primer campo (id) de la línea
            parts = line.split('\t')
            expected_cols = len(social_columns) if social_columns else 0
            if len(parts) > 1:
                # Remover el primer campo (id) y unir el resto
                data_without_id = '\t'.join(parts[1:])
                # Validar que tengamos el número correcto de campos
                remaining_parts = parts[1:]
                if expected_cols > 0 and len(remaining_parts) != expected_cols:
                    # Ajustar: si faltan campos, agregar NULLs; si sobran, truncar
                    if len(remaining_parts) < expected_cols:
                        remaining_parts.extend(['\\N'] * (expected_cols - len(remaining_parts)))
                    elif len(remaining_parts) > expected_cols:
                        remaining_parts = remaining_parts[:expected_cols]
                    data_without_id = '\t'.join(remaining_parts)
                social_news_data.append(data_without_id)
    
    print(f"   ✅ Datos extraídos:")
    print(f"      - Noticias: {len(noticias_data)} registros")
    print(f"      - Social news: {len(social_news_data)} registros")
    
    return noticias_data, social_news_data, noticias_columns, social_columns


def get_table_columns(table_name):
    """Obtiene las columnas reales de una tabla"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return columns
    except Exception as e:
        print(f"   ⚠️  Error obteniendo columnas de {table_name}: {e}")
        return []


def restore_backup():
    """Restaura el backup usando psycopg2 COPY directamente"""
    print("\n📦 Iniciando restauración de backup...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Obtener columnas reales de las tablas
        print("\n🔍 Verificando estructura de las tablas...")
        noticias_real_columns = get_table_columns('noticias')
        social_news_real_columns = get_table_columns('social_news')
        
        print(f"   📋 Columnas en tabla 'noticias': {', '.join(noticias_real_columns)}")
        print(f"   📋 Columnas en tabla 'social_news': {', '.join(social_news_real_columns)}")
        
        # Contar registros antes
        cursor.execute("SELECT COUNT(*) FROM noticias")
        count_before_noticias = cursor.fetchone()[0]
        
        try:
            cursor.execute("SELECT COUNT(*) FROM social_news")
            count_before_social = cursor.fetchone()[0]
        except:
            count_before_social = 0
        
        print(f"\n📊 Registros antes de la restauración:")
        print(f"   - Noticias: {count_before_noticias}")
        print(f"   - Social news: {count_before_social}")
        
        # Solo remover constraint UNIQUE de URL temporalmente para evitar errores
        # Mantener PRIMARY KEY y DEFAULT para generar IDs automáticamente
        print("\n🔧 Preparando base de datos para restauración...")
        
        try:
            cursor.execute("ALTER TABLE noticias DROP CONSTRAINT IF EXISTS noticias_url_key;")
            print("   ✅ Constraint UNIQUE de URL removida temporalmente en 'noticias'")
        except Exception as e:
            print(f"   ⚠️  No se pudo remover constraint de noticias: {e}")
        
        try:
            cursor.execute("ALTER TABLE social_news DROP CONSTRAINT IF EXISTS social_news_url_key;")
            print("   ✅ Constraint UNIQUE de URL removida temporalmente en 'social_news'")
        except Exception as e:
            print(f"   ⚠️  No se pudo remover constraint de social_news: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Extraer y procesar datos (sin el campo id)
        noticias_data, social_news_data, noticias_columns_backup, social_columns_backup = extract_and_process_data()
        
        if not noticias_data and not social_news_data:
            print("❌ Error: No se encontraron datos para restaurar en el backup")
            return False
        
        # Mapear columnas del backup a las de la tabla local
        # Necesitamos crear un mapeo de índices para ajustar los datos
        def create_column_mapping(backup_cols, real_cols):
            """Crea un mapeo de índices: qué columnas del backup usar y en qué orden"""
            # Remover 'id' de ambas listas si está presente
            backup_cols_no_id = [col for col in backup_cols if col != 'id']
            real_cols_no_id = [col for col in real_cols if col != 'id']
            
            # Crear mapeo: para cada columna en real_cols, encontrar su índice en backup_cols
            mapping = []
            for real_col in real_cols_no_id:
                if real_col in backup_cols_no_id:
                    mapping.append((backup_cols_no_id.index(real_col), real_col))
                else:
                    # Columna no existe en backup, será NULL
                    mapping.append((None, real_col))
            
            return mapping, [col for _, col in mapping]
        
        if noticias_columns_backup and noticias_real_columns:
            noticias_mapping, noticias_columns_filtered = create_column_mapping(
                noticias_columns_backup, noticias_real_columns
            )
            print(f"\n   🔄 Columnas de noticias mapeadas: {len(noticias_columns_filtered)} columnas")
            excluded = set(noticias_columns_backup) - set(noticias_real_columns) - {'id'}
            if excluded:
                print(f"      ⚠️  Columnas del backup excluidas (no existen en tabla local): {', '.join(excluded)}")
            noticias_columns_backup = noticias_columns_filtered
        else:
            noticias_mapping = []
        
        if social_columns_backup and social_news_real_columns:
            social_mapping, social_columns_filtered = create_column_mapping(
                social_columns_backup, social_news_real_columns
            )
            print(f"   🔄 Columnas de social_news mapeadas: {len(social_columns_filtered)} columnas")
            excluded = set(social_columns_backup) - set(social_news_real_columns) - {'id'}
            if excluded:
                print(f"      ⚠️  Columnas del backup excluidas (no existen en tabla local): {', '.join(excluded)}")
            social_columns_backup = social_columns_filtered
        else:
            social_mapping = []
        
        # Usar psycopg2 COPY directamente para mejor control
        print(f"\n🔄 Insertando datos usando COPY (esto puede tomar varios minutos)...")
        
        # Reconectar para COPY
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        inserted_noticias = 0
        inserted_social = 0
        
        # Insertar noticias
        if noticias_data and noticias_columns_backup:
            print(f"   📝 Insertando {len(noticias_data)} registros de noticias...")
            try:
                # Crear un StringIO con los datos
                from io import StringIO
                data_stream = StringIO()
                
                # Escribir datos al stream usando el mapeo de columnas
                for i, data_line in enumerate(noticias_data):
                    parts = data_line.split('\t')
                    # Usar el mapeo para reordenar y filtrar columnas
                    mapped_parts = []
                    for backup_idx, real_col in noticias_mapping:
                        if backup_idx is not None and backup_idx < len(parts):
                            mapped_parts.append(parts[backup_idx])
                        else:
                            # Columna no existe en backup, usar NULL
                            mapped_parts.append('\\N')
                    data_stream.write('\t'.join(mapped_parts) + '\n')
                    
                    if (i + 1) % 1000 == 0:
                        print(f"      - Procesadas {i + 1} líneas...")
                
                data_stream.seek(0)
                
                # Usar COPY FROM con el stream
                cursor.copy_from(
                    data_stream,
                    'noticias',
                    columns=noticias_columns_backup,
                    sep='\t',
                    null='\\N'
                )
                inserted_noticias = len(noticias_data)
                print(f"   ✅ {inserted_noticias} registros de noticias insertados")
            except Exception as e:
                print(f"   ❌ Error insertando noticias: {e}")
                import traceback
                traceback.print_exc()
                conn.rollback()
        
        # Insertar social_news
        if social_news_data and social_columns_backup:
            print(f"   📝 Insertando {len(social_news_data)} registros de social_news...")
            try:
                from io import StringIO
                data_stream = StringIO()
                
                for data_line in social_news_data:
                    parts = data_line.split('\t')
                    # Usar el mapeo para reordenar y filtrar columnas
                    mapped_parts = []
                    for backup_idx, real_col in social_mapping:
                        if backup_idx is not None and backup_idx < len(parts):
                            mapped_parts.append(parts[backup_idx])
                        else:
                            # Columna no existe en backup, usar NULL
                            mapped_parts.append('\\N')
                    data_stream.write('\t'.join(mapped_parts) + '\n')
                
                data_stream.seek(0)
                
                cursor.copy_from(
                    data_stream,
                    'social_news',
                    columns=social_columns_backup,
                    sep='\t',
                    null='\\N'
                )
                inserted_social = len(social_news_data)
                print(f"   ✅ {inserted_social} registros de social_news insertados")
            except Exception as e:
                print(f"   ❌ Error insertando social_news: {e}")
                import traceback
                traceback.print_exc()
                conn.rollback()
        
        conn.commit()
        
        # Limpiar duplicados y restaurar constraints
        print("\n🔧 Limpiando duplicados y restaurando constraints...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Contar registros después de la restauración
        cursor.execute("SELECT COUNT(*) FROM noticias")
        count_after_restore_noticias = cursor.fetchone()[0]
        
        try:
            cursor.execute("SELECT COUNT(*) FROM social_news")
            count_after_restore_social = cursor.fetchone()[0]
        except:
            count_after_restore_social = count_before_social
        
        restored_noticias = count_after_restore_noticias - count_before_noticias
        restored_social = count_after_restore_social - count_before_social
        
        print(f"\n📊 Registros después de la restauración:")
        print(f"   - Noticias: {count_after_restore_noticias} (+{restored_noticias})")
        print(f"   - Social news: {count_after_restore_social} (+{restored_social})")
        
        # Actualizar duplicados por URL (reemplazar datos del más antiguo con los del más reciente)
        print("\n   🔄 Actualizando duplicados por URL (reemplazando con datos más recientes, especialmente imágenes)...")
        
        # Para noticias: actualizar el registro más antiguo con los datos del más reciente
        cursor.execute("""
            UPDATE noticias old
            SET 
                titulo = new.titulo,
                fecha = new.fecha,
                resumen = new.resumen,
                contenido = new.contenido,
                categoria = new.categoria,
                autor = new.autor,
                tags = new.tags,
                fecha_extraccion = new.fecha_extraccion,
                caracteres_contenido = new.caracteres_contenido,
                palabras_contenido = new.palabras_contenido,
                imagenes = new.imagenes,
                fuente = new.fuente
            FROM noticias new
            WHERE old.url = new.url 
            AND new.id = (
                SELECT MAX(id) 
                FROM noticias 
                WHERE url = old.url
            )
            AND old.id < new.id;
        """)
        updated_noticias = cursor.rowcount
        
        # Eliminar los registros duplicados más recientes (ya que sus datos están en el más antiguo)
        cursor.execute("""
            DELETE FROM noticias a
            USING noticias b
            WHERE a.url = b.url 
            AND a.id > b.id;
        """)
        deleted_noticias = cursor.rowcount
        
        # Para social_news: actualizar el registro más antiguo con los datos del más reciente
        try:
            cursor.execute("""
                UPDATE social_news old
                SET 
                    titulo = new.titulo,
                    fecha = new.fecha,
                    resumen = new.resumen,
                    contenido = new.contenido,
                    categoria = new.categoria,
                    autor = new.autor,
                    tags = new.tags,
                    fecha_extraccion = new.fecha_extraccion,
                    imagenes = new.imagenes,
                    fuente = new.fuente
                FROM social_news new
                WHERE old.url = new.url 
                AND new.id = (
                    SELECT MAX(id) 
                    FROM social_news 
                    WHERE url = old.url
                )
                AND old.id < new.id;
            """)
            updated_social = cursor.rowcount
            
            # Eliminar los registros duplicados más recientes
            cursor.execute("""
                DELETE FROM social_news a
                USING social_news b
                WHERE a.url = b.url 
                AND a.id > b.id;
            """)
            deleted_social = cursor.rowcount
        except Exception as e:
            print(f"      ⚠️  Error procesando social_news: {e}")
            updated_social = 0
            deleted_social = 0
        
        if updated_noticias > 0:
            print(f"      - Actualizados {updated_noticias} registros duplicados en 'noticias' (campo imagenes reemplazado)")
        if deleted_noticias > 0:
            print(f"      - Eliminados {deleted_noticias} registros duplicados en 'noticias'")
        if updated_social > 0:
            print(f"      - Actualizados {updated_social} registros duplicados en 'social_news' (campo imagenes reemplazado)")
        if deleted_social > 0:
            print(f"      - Eliminados {deleted_social} registros duplicados en 'social_news'")
        
        # Ajustar secuencias al máximo ID existente
        print("\n   🔄 Ajustando secuencias de IDs...")
        
        # Para noticias
        try:
            cursor.execute("SELECT COALESCE(MAX(id), 0) FROM noticias;")
            max_id = cursor.fetchone()[0]
            cursor.execute(f"SELECT setval('noticias_id_seq', {max_id + 1}, true);")
            print(f"   ✅ Secuencia de 'noticias' ajustada a {max_id + 1}")
        except Exception as e:
            print(f"   ⚠️  No se pudo ajustar secuencia de noticias: {e}")
        
        # Para social_news
        try:
            cursor.execute("SELECT COALESCE(MAX(id), 0) FROM social_news;")
            max_id = cursor.fetchone()[0]
            cursor.execute(f"SELECT setval('social_news_id_seq', {max_id + 1}, true);")
            print(f"   ✅ Secuencia de 'social_news' ajustada a {max_id + 1}")
        except Exception as e:
            print(f"   ⚠️  No se pudo ajustar secuencia de social_news: {e}")
        
        # Restaurar constraint UNIQUE de URL
        print("\n   🔄 Restaurando constraint UNIQUE de URL...")
        
        try:
            cursor.execute("""
                ALTER TABLE noticias 
                ADD CONSTRAINT noticias_url_key UNIQUE (url);
            """)
            print("   ✅ Constraint UNIQUE de URL restaurada en 'noticias'")
        except Exception as e:
            print(f"   ⚠️  No se pudo restaurar constraint de noticias: {e}")
        
        try:
            cursor.execute("""
                ALTER TABLE social_news 
                ADD CONSTRAINT social_news_url_key UNIQUE (url);
            """)
            print("   ✅ Constraint UNIQUE de URL restaurada en 'social_news'")
        except Exception as e:
            print(f"   ⚠️  No se pudo restaurar constraint de social_news: {e}")
        
        conn.commit()
        
        # Contar registros finales después de limpiar duplicados
        cursor.execute("SELECT COUNT(*) FROM noticias")
        count_after_noticias = cursor.fetchone()[0]
        
        try:
            cursor.execute("SELECT COUNT(*) FROM social_news")
            count_after_social = cursor.fetchone()[0]
        except:
            count_after_social = count_before_social
        
        inserted_noticias = count_after_noticias - count_before_noticias
        inserted_social = count_after_social - count_before_social
        
        cursor.close()
        conn.close()
        
        # Resumen final
        print(f"\n✅ Restauración completada:")
        print(f"\n📊 Resumen final:")
        print(f"   - Noticias:")
        print(f"     • Registros antes: {count_before_noticias}")
        print(f"     • Registros insertados del backup: {restored_noticias}")
        print(f"     • Duplicados actualizados (con nuevas imágenes): {updated_noticias}")
        print(f"     • Duplicados eliminados (por URL): {deleted_noticias}")
        print(f"     • Registros finales: {count_after_noticias}")
        print(f"     • Neto agregado: {inserted_noticias} registros nuevos")
        print(f"   - Social news:")
        print(f"     • Registros antes: {count_before_social}")
        print(f"     • Registros insertados del backup: {restored_social}")
        print(f"     • Duplicados actualizados (con nuevas imágenes): {updated_social}")
        print(f"     • Duplicados eliminados (por URL): {deleted_social}")
        print(f"     • Registros finales: {count_after_social}")
        print(f"     • Neto agregado: {inserted_social} registros nuevos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en restauración: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal"""
    print("=" * 60)
    print("🔄 RESTAURACIÓN DE BACKUP A BASE DE DATOS LOCAL")
    print("=" * 60)
    print(f"\n📁 Archivo de backup: {BACKUP_FILE}")
    print(f"🗄️  Base de datos: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print()
    
    # Verificaciones
    if not check_backup_file():
        sys.exit(1)
    
    if not test_connection():
        print("\n💡 Sugerencia: Verifica que PostgreSQL esté corriendo y las credenciales sean correctas")
        sys.exit(1)
    
    if not check_tables_exist():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🚀 Iniciando restauración...")
    print("=" * 60)
    
    # Restaurar backup
    success = restore_backup()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ RESTAURACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ LA RESTAURACIÓN FALLÓ")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

