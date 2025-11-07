#!/usr/bin/env python3
"""
Script para crear la tabla noticias_limpia y cargar los datos procesados
"""

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

def create_clean_table(conn):
    """Crear la tabla noticias_limpia"""
    cursor = conn.cursor()
    
    # Definir la estructura de la tabla
    create_table_query = """
    CREATE TABLE IF NOT EXISTS noticias_limpia (
        id SERIAL PRIMARY KEY,
        titulo TEXT NOT NULL,
        fecha DATE,
        hora TIME,
        anio FLOAT,
        mes FLOAT,
        dia FLOAT,
        dia_semana VARCHAR(20),
        resumen TEXT,
        contenido TEXT,
        categoria VARCHAR(100),
        autor VARCHAR(255),
        keywords TEXT,
        url TEXT NOT NULL UNIQUE,
        dominio VARCHAR(255),
        fecha_extraccion TIMESTAMP,
        imagen_principal TEXT,
        cantidad_imagenes INTEGER,
        tiene_imagenes BOOLEAN,
        fuente VARCHAR(100),
        longitud_titulo INTEGER,
        longitud_resumen FLOAT,
        tipo_contenido VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        cursor.execute(create_table_query)
        conn.commit()
        print("✅ Tabla 'noticias_limpia' creada exitosamente")
        return True
    except psycopg2.Error as e:
        print(f"Error creando tabla: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def load_clean_data(conn, csv_file):
    """Cargar datos del CSV procesado a la tabla noticias_limpia"""
    try:
        # Leer el CSV
        df = pd.read_csv(csv_file)
        print(f"📊 Cargando {len(df)} registros del archivo {csv_file}")
        
        # Limpiar datos antes de insertar
        df = df.fillna('')  # Reemplazar NaN con strings vacíos
        
        # Convertir fechas vacías a None
        df['fecha'] = df['fecha'].replace('', None)
        df['hora'] = df['hora'].replace('', None)
        df['fecha_extraccion'] = df['fecha_extraccion'].replace('', None)
        df['created_at'] = df['created_at'].replace('', None)
        
        cursor = conn.cursor()
        
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
        ON CONFLICT (url) DO UPDATE SET
            titulo = EXCLUDED.titulo,
            fecha = EXCLUDED.fecha,
            hora = EXCLUDED.hora,
            anio = EXCLUDED.anio,
            mes = EXCLUDED.mes,
            dia = EXCLUDED.dia,
            dia_semana = EXCLUDED.dia_semana,
            resumen = EXCLUDED.resumen,
            contenido = EXCLUDED.contenido,
            categoria = EXCLUDED.categoria,
            autor = EXCLUDED.autor,
            keywords = EXCLUDED.keywords,
            dominio = EXCLUDED.dominio,
            fecha_extraccion = EXCLUDED.fecha_extraccion,
            imagen_principal = EXCLUDED.imagen_principal,
            cantidad_imagenes = EXCLUDED.cantidad_imagenes,
            tiene_imagenes = EXCLUDED.tiene_imagenes,
            fuente = EXCLUDED.fuente,
            longitud_titulo = EXCLUDED.longitud_titulo,
            longitud_resumen = EXCLUDED.longitud_resumen,
            tipo_contenido = EXCLUDED.tipo_contenido,
            created_at = EXCLUDED.created_at
        """
        
        # Convertir DataFrame a lista de tuplas
        data_tuples = []
        for _, row in df.iterrows():
            # Validar fecha
            fecha_val = None
            if pd.notna(row['fecha']) and str(row['fecha']).strip() != '':
                try:
                    fecha_val = pd.to_datetime(row['fecha']).date()
                except:
                    fecha_val = None
            
            # Validar hora
            hora_val = None
            if pd.notna(row['hora']) and str(row['hora']).strip() != '':
                try:
                    hora_val = pd.to_datetime(row['hora']).time()
                except:
                    hora_val = None
            
            # Validar fecha_extraccion
            fecha_extraccion_val = None
            if pd.notna(row['fecha_extraccion']) and str(row['fecha_extraccion']).strip() != '':
                try:
                    fecha_extraccion_val = pd.to_datetime(row['fecha_extraccion'])
                except:
                    fecha_extraccion_val = None
            
            # Validar created_at
            created_at_val = None
            if pd.notna(row['created_at']) and str(row['created_at']).strip() != '':
                try:
                    created_at_val = pd.to_datetime(row['created_at'])
                except:
                    created_at_val = None
            
            data_tuples.append((
                str(row['titulo']),
                fecha_val,
                hora_val,
                float(row['anio']) if pd.notna(row['anio']) and str(row['anio']).strip() != '' else None,
                float(row['mes']) if pd.notna(row['mes']) and str(row['mes']).strip() != '' else None,
                float(row['dia']) if pd.notna(row['dia']) and str(row['dia']).strip() != '' else None,
                str(row['dia_semana']) if pd.notna(row['dia_semana']) else None,
                str(row['resumen']) if pd.notna(row['resumen']) else None,
                str(row['contenido']) if pd.notna(row['contenido']) else None,
                str(row['categoria']) if pd.notna(row['categoria']) else None,
                str(row['autor']) if pd.notna(row['autor']) else None,
                str(row['keywords']) if pd.notna(row['keywords']) else None,
                str(row['url']),
                str(row['dominio']) if pd.notna(row['dominio']) else None,
                fecha_extraccion_val,
                str(row['imagen_principal']) if pd.notna(row['imagen_principal']) else None,
                int(row['cantidad_imagenes']) if pd.notna(row['cantidad_imagenes']) and str(row['cantidad_imagenes']).strip() != '' else None,
                bool(row['tiene_imagenes']) if pd.notna(row['tiene_imagenes']) and str(row['tiene_imagenes']).strip() != '' else None,
                str(row['fuente']),
                int(row['longitud_titulo']) if pd.notna(row['longitud_titulo']) and str(row['longitud_titulo']).strip() != '' else None,
                float(row['longitud_resumen']) if pd.notna(row['longitud_resumen']) and str(row['longitud_resumen']).strip() != '' else None,
                str(row['tipo_contenido']) if pd.notna(row['tipo_contenido']) else None,
                created_at_val
            ))
        
        # Insertar en lotes
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(data_tuples), batch_size):
            batch = data_tuples[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            conn.commit()
            total_inserted += len(batch)
            print(f"📝 Procesados {total_inserted}/{len(data_tuples)} registros...")
        
        print(f"✅ {total_inserted} registros cargados exitosamente en noticias_limpia")
        return True
        
    except Exception as e:
        print(f"Error cargando datos: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def verify_data(conn):
    """Verificar los datos cargados"""
    cursor = conn.cursor()
    
    try:
        # Contar registros
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
        
        # Contar por categoría
        cursor.execute("""
            SELECT categoria, COUNT(*) as cantidad 
            FROM noticias_limpia 
            WHERE categoria IS NOT NULL AND categoria != ''
            GROUP BY categoria 
            ORDER BY cantidad DESC
            LIMIT 10
        """)
        categorias = cursor.fetchall()
        
        print(f"\n=== VERIFICACIÓN DE DATOS CARGADOS ===")
        print(f"📊 Total de registros: {total_count}")
        
        print(f"\n📰 Distribución por fuente:")
        for fuente, cantidad in fuentes:
            print(f"   - {fuente}: {cantidad}")
        
        print(f"\n🏷️  Top categorías:")
        for categoria, cantidad in categorias:
            print(f"   - {categoria}: {cantidad}")
        
        # Mostrar algunas noticias de ejemplo
        cursor.execute("""
            SELECT titulo, fuente, categoria, fecha 
            FROM noticias_limpia 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        ejemplos = cursor.fetchall()
        
        print(f"\n🔍 Ejemplos de noticias cargadas:")
        for i, (titulo, fuente, categoria, fecha) in enumerate(ejemplos, 1):
            print(f"{i}. [{fuente}] {titulo[:60]}...")
            print(f"   Categoría: {categoria} | Fecha: {fecha}")
        
        return True
        
    except Exception as e:
        print(f"Error verificando datos: {e}")
        return False
    finally:
        cursor.close()

def main():
    print("=== CREACIÓN DE TABLA NOTICIAS_LIMPIA ===")
    
    # Conectar a la base de datos
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        # Crear tabla
        if not create_clean_table(conn):
            return False
        
        # Cargar datos
        csv_file = "data_etl_final_20251014_070213.csv"
        if not load_clean_data(conn, csv_file):
            return False
        
        # Verificar datos
        verify_data(conn)
        
        print(f"\n✅ Proceso completado exitosamente")
        print(f"   Tabla 'noticias_limpia' creada y poblada con datos procesados")
        
        return True
        
    except Exception as e:
        print(f"Error en el proceso: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
