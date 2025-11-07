#!/usr/bin/env python3
"""
Script para integrar nuevas noticias en la tabla noticias_limpia
con filtro de duplicados por URL
"""

import glob
import os
from datetime import datetime

import pandas as pd
import psycopg2


def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='noticias',
            user='postgres',
            password='123456',
            port='5432'
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def get_existing_urls(conn):
    """Obtener URLs existentes en noticias_limpia"""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT url FROM noticias_limpia")
        existing_urls = set(row[0] for row in cursor.fetchall())
        print(f"📊 URLs existentes en noticias_limpia: {len(existing_urls)}")
        return existing_urls
    except Exception as e:
        print(f"Error obteniendo URLs existentes: {e}")
        return set()
    finally:
        cursor.close()

def find_new_csv_files():
    """Encontrar archivos CSV nuevos para procesar"""
    # Buscar archivos CSV en el directorio etl-data
    csv_patterns = [
        "data_etl_final_*.csv",
        "noticias_*.csv",
        "export_*.csv"
    ]
    
    csv_files = []
    for pattern in csv_patterns:
        csv_files.extend(glob.glob(pattern))
    
    # Filtrar archivos que no sean el original ya procesado
    new_files = []
    for file in csv_files:
        if "data_etl_final_20251014_063022" not in file:
            new_files.append(file)
    
    return new_files

def process_csv_file(conn, csv_file, existing_urls):
    """Procesar un archivo CSV y extraer noticias nuevas"""
    try:
        print(f"\n📁 Procesando archivo: {csv_file}")
        
        # Leer el CSV
        df = pd.read_csv(csv_file)
        print(f"📊 Total de registros en archivo: {len(df)}")
        
        # Verificar si tiene la estructura correcta
        required_columns = ['titulo', 'url', 'fuente']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️  Archivo {csv_file} no tiene las columnas requeridas: {missing_columns}")
            return pd.DataFrame()
        
        # Filtrar noticias nuevas (que no estén en la base de datos)
        df_new = df[~df['url'].isin(existing_urls)]
        print(f"🆕 Noticias nuevas encontradas: {len(df_new)}")
        
        if len(df_new) == 0:
            print("ℹ️  No hay noticias nuevas en este archivo")
            return pd.DataFrame()
        
        # Aplicar transformaciones ETL básicas si no están presentes
        df_new = apply_basic_etl(df_new)
        
        return df_new
        
    except Exception as e:
        print(f"❌ Error procesando archivo {csv_file}: {e}")
        return pd.DataFrame()

def apply_basic_etl(df):
    """Aplicar transformaciones ETL básicas"""
    try:
        # Limpiar datos
        df = df.fillna('')
        
        # Agregar columnas faltantes si no existen
        if 'anio' not in df.columns:
            df['anio'] = pd.to_datetime(df['fecha'], errors='coerce').dt.year
        if 'mes' not in df.columns:
            df['mes'] = pd.to_datetime(df['fecha'], errors='coerce').dt.month
        if 'dia' not in df.columns:
            df['dia'] = pd.to_datetime(df['fecha'], errors='coerce').dt.day
        if 'dia_semana' not in df.columns:
            df['dia_semana'] = pd.to_datetime(df['fecha'], errors='coerce').dt.day_name()
        if 'keywords' not in df.columns:
            df['keywords'] = df['titulo'].str.lower().str.replace('[^\w\s]', '', regex=True).str.split().str[:5].str.join(', ')
        if 'dominio' not in df.columns:
            df['dominio'] = df['url'].str.extract(r'https?://([^/]+)')
        if 'imagen_principal' not in df.columns:
            df['imagen_principal'] = ''
        if 'cantidad_imagenes' not in df.columns:
            df['cantidad_imagenes'] = 0
        if 'tiene_imagenes' not in df.columns:
            df['tiene_imagenes'] = False
        if 'longitud_titulo' not in df.columns:
            df['longitud_titulo'] = df['titulo'].str.len()
        if 'longitud_resumen' not in df.columns:
            df['longitud_resumen'] = df['resumen'].str.len()
        if 'tipo_contenido' not in df.columns:
            df['tipo_contenido'] = 'Noticia'
        if 'created_at' not in df.columns:
            df['created_at'] = datetime.now()
        
        return df
        
    except Exception as e:
        print(f"Error aplicando ETL básico: {e}")
        return df

def insert_new_news(conn, df_new):
    """Insertar noticias nuevas en la tabla noticias_limpia"""
    if df_new.empty:
        return 0
    
    cursor = conn.cursor()
    
    try:
        # Preparar datos para inserción
        insert_query = """
        INSERT INTO noticias_limpia (
            titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido,
            categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
            cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
            tipo_contenido, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        # Convertir DataFrame a lista de tuplas
        data_tuples = []
        for _, row in df_new.iterrows():
            # Validar fecha
            fecha_val = None
            if pd.notna(row.get('fecha', '')) and str(row.get('fecha', '')).strip() != '':
                try:
                    fecha_val = pd.to_datetime(row['fecha']).date()
                except:
                    fecha_val = None
            
            # Validar hora
            hora_val = None
            if pd.notna(row.get('hora', '')) and str(row.get('hora', '')).strip() != '':
                try:
                    hora_val = pd.to_datetime(row['hora']).time()
                except:
                    hora_val = None
            
            # Validar fecha_extraccion
            fecha_extraccion_val = None
            if pd.notna(row.get('fecha_extraccion', '')) and str(row.get('fecha_extraccion', '')).strip() != '':
                try:
                    fecha_extraccion_val = pd.to_datetime(row['fecha_extraccion'])
                except:
                    fecha_extraccion_val = None
            
            # Validar created_at
            created_at_val = None
            if pd.notna(row.get('created_at', '')) and str(row.get('created_at', '')).strip() != '':
                try:
                    created_at_val = pd.to_datetime(row['created_at'])
                except:
                    created_at_val = datetime.now()
            
            data_tuples.append((
                str(row.get('titulo', '')),
                fecha_val,
                hora_val,
                float(row.get('anio', 0)) if pd.notna(row.get('anio', 0)) and str(row.get('anio', 0)).strip() != '' else None,
                float(row.get('mes', 0)) if pd.notna(row.get('mes', 0)) and str(row.get('mes', 0)).strip() != '' else None,
                float(row.get('dia', 0)) if pd.notna(row.get('dia', 0)) and str(row.get('dia', 0)).strip() != '' else None,
                str(row.get('dia_semana', '')) if pd.notna(row.get('dia_semana', '')) else None,
                str(row.get('resumen', '')) if pd.notna(row.get('resumen', '')) else None,
                str(row.get('contenido', '')) if pd.notna(row.get('contenido', '')) else None,
                str(row.get('categoria', '')) if pd.notna(row.get('categoria', '')) else None,
                str(row.get('autor', '')) if pd.notna(row.get('autor', '')) else None,
                str(row.get('keywords', '')) if pd.notna(row.get('keywords', '')) else None,
                str(row.get('url', '')),
                str(row.get('dominio', '')) if pd.notna(row.get('dominio', '')) else None,
                fecha_extraccion_val,
                str(row.get('imagen_principal', '')) if pd.notna(row.get('imagen_principal', '')) else None,
                int(row.get('cantidad_imagenes', 0)) if pd.notna(row.get('cantidad_imagenes', 0)) and str(row.get('cantidad_imagenes', 0)).strip() != '' else None,
                bool(row.get('tiene_imagenes', False)) if pd.notna(row.get('tiene_imagenes', False)) and str(row.get('tiene_imagenes', False)).strip() != '' else None,
                str(row.get('fuente', '')),
                int(row.get('longitud_titulo', 0)) if pd.notna(row.get('longitud_titulo', 0)) and str(row.get('longitud_titulo', 0)).strip() != '' else None,
                float(row.get('longitud_resumen', 0)) if pd.notna(row.get('longitud_resumen', 0)) and str(row.get('longitud_resumen', 0)).strip() != '' else None,
                str(row.get('tipo_contenido', 'Noticia')) if pd.notna(row.get('tipo_contenido', 'Noticia')) else None,
                created_at_val
            ))
        
        # Insertar en lotes
        batch_size = 50
        total_inserted = 0
        
        for i in range(0, len(data_tuples), batch_size):
            batch = data_tuples[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            conn.commit()
            total_inserted += len(batch)
            print(f"📝 Insertados {total_inserted}/{len(data_tuples)} registros...")
        
        print(f"✅ {total_inserted} noticias nuevas insertadas exitosamente")
        return total_inserted
        
    except Exception as e:
        print(f"❌ Error insertando noticias: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()

def verify_integration(conn):
    """Verificar la integración de nuevas noticias"""
    cursor = conn.cursor()
    
    try:
        # Contar registros totales
        cursor.execute("SELECT COUNT(*) FROM noticias_limpia")
        total_count = cursor.fetchone()[0]
        
        # Contar por fuente
        cursor.execute("""
            SELECT fuente, COUNT(*) as cantidad 
            FROM noticias_limpia 
            GROUP BY fuente 
            ORDER BY cantidad DESC
        """)
        fuentes = cursor.fetchall()
        
        # Mostrar noticias más recientes
        cursor.execute("""
            SELECT titulo, fuente, categoria, created_at 
            FROM noticias_limpia 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recientes = cursor.fetchall()
        
        print(f"\n=== VERIFICACIÓN POST-INTEGRACIÓN ===")
        print(f"📊 Total de registros: {total_count}")
        
        print(f"\n📰 Distribución por fuente:")
        for fuente, cantidad in fuentes:
            print(f"   - {fuente}: {cantidad}")
        
        print(f"\n🔍 Noticias más recientes:")
        for i, (titulo, fuente, categoria, created_at) in enumerate(recientes, 1):
            print(f"{i}. [{fuente}] {titulo[:60]}...")
            print(f"   Categoría: {categoria} | Creada: {created_at}")
        
        return True
        
    except Exception as e:
        print(f"Error verificando integración: {e}")
        return False
    finally:
        cursor.close()

def main():
    print("=== INTEGRACIÓN DE NUEVAS NOTICIAS ===")
    
    # Conectar a la base de datos
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        # Obtener URLs existentes
        existing_urls = get_existing_urls(conn)
        
        # Buscar archivos CSV nuevos
        new_files = find_new_csv_files()
        
        if not new_files:
            print("ℹ️  No se encontraron archivos CSV nuevos para procesar")
            return True
        
        print(f"📁 Archivos encontrados: {len(new_files)}")
        for file in new_files:
            print(f"   - {file}")
        
        total_new_news = 0
        
        # Procesar cada archivo
        for csv_file in new_files:
            df_new = process_csv_file(conn, csv_file, existing_urls)
            
            if not df_new.empty:
                inserted = insert_new_news(conn, df_new)
                total_new_news += inserted
                
                # Actualizar URLs existentes para evitar duplicados en el mismo lote
                new_urls = set(df_new['url'].tolist())
                existing_urls.update(new_urls)
        
        # Verificar integración
        verify_integration(conn)
        
        print(f"\n✅ Integración completada exitosamente")
        print(f"   Total de noticias nuevas agregadas: {total_new_news}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en el proceso de integración: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
