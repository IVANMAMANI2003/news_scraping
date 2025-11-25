#!/usr/bin/env python3
"""
Script completo para migrar datos de 'noticias' a 'noticias_limpia'
Automatiza todo el proceso: exportar, normalizar y cargar
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Cambiar al directorio del script para que los imports funcionen
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# Agregar el directorio actual al path para importar módulos
sys.path.insert(0, str(script_dir))

try:
    import numpy as np
    import pandas as pd
except ImportError as e:
    print("❌ Error: pandas y numpy no están instalados")
    print(f"   Error detallado: {e}")
    print("   Ejecuta: pip install pandas numpy")
    print(f"   Directorio actual: {os.getcwd()}")
    print(f"   Python: {sys.executable}")
    sys.exit(1)

import psycopg2

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'noticias',
    'user': 'postgres',
    'password': '123456'
}


def export_noticias_to_csv():
    """Paso 1: Exportar datos de noticias a CSV"""
    print("\n" + "=" * 60)
    print("📤 PASO 1: Exportando datos de 'noticias' a CSV")
    print("=" * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"noticias_{timestamp}.csv"
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Obtener datos
        cursor.execute("""
            SELECT 
                id, titulo, fecha, resumen, contenido, categoria, autor, 
                tags, url, fecha_extraccion, imagenes, fuente, created_at
            FROM noticias 
            ORDER BY fecha_extraccion DESC
        """)
        
        # Crear DataFrame
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        
        # Guardar CSV
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        cursor.close()
        conn.close()
        
        print(f"✅ Exportación completada: {len(df)} registros")
        print(f"📁 Archivo: {output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error exportando: {e}")
        import traceback
        traceback.print_exc()
        return None


def normalize_data(input_file):
    """Paso 2: Normalizar datos usando data-normalizer"""
    print("\n" + "=" * 60)
    print("🔄 PASO 2: Normalizando datos")
    print("=" * 60)
    
    try:
        # Importar el normalizador (el archivo tiene guión, usar importlib)
        import importlib.util
        normalizer_path = script_dir / "data-normalizer.py"
        spec = importlib.util.spec_from_file_location("data_normalizer", str(normalizer_path))
        data_normalizer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_normalizer)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data_etl_final_{timestamp}.csv"
        
        # Ejecutar ETL
        etl = data_normalizer.NewsETL()
        df_final = etl.run_etl(input_file, output_file)
        
        if df_final is not None:
            print(f"✅ Normalización completada: {len(df_final)} registros")
            print(f"📁 Archivo: {output_file}")
            return output_file
        else:
            print("❌ Error en la normalización")
            return None
            
    except Exception as e:
        print(f"❌ Error normalizando: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_and_load_clean_table(csv_file):
    """Paso 3: Crear tabla noticias_limpia y cargar datos"""
    print("\n" + "=" * 60)
    print("📥 PASO 3: Creando tabla 'noticias_limpia' y cargando datos")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Crear tabla
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
        
        cursor.execute(create_table_query)
        conn.commit()
        print("✅ Tabla 'noticias_limpia' creada/verificada")
        
        # Leer CSV
        df = pd.read_csv(csv_file)
        print(f"📊 Cargando {len(df)} registros del archivo {csv_file}")
        
        # Limpiar datos
        df = df.fillna('')
        
        # Contar registros existentes antes
        cursor.execute("SELECT COUNT(*) FROM noticias_limpia")
        count_before = cursor.fetchone()[0]
        print(f"📊 Registros existentes en 'noticias_limpia': {count_before}")
        
        # Preparar query de inserción
        # ON CONFLICT DO NOTHING: solo inserta nuevos registros, no actualiza ni elimina existentes
        # El campo 'id' NO se incluye - se genera automáticamente de forma incremental (SERIAL)
        insert_query = """
        INSERT INTO noticias_limpia (
            titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido,
            categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
            cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
            tipo_contenido, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (url) DO NOTHING
        """
        
        # Preparar datos
        data_tuples = []
        for _, row in df.iterrows():
            # Convertir fechas
            fecha_val = None
            if pd.notna(row.get('fecha')) and str(row.get('fecha', '')).strip() != '':
                try:
                    fecha_val = pd.to_datetime(row['fecha']).date()
                except:
                    fecha_val = None
            
            hora_val = None
            if pd.notna(row.get('hora')) and str(row.get('hora', '')).strip() != '':
                try:
                    hora_val = pd.to_datetime(row['hora']).time()
                except:
                    hora_val = None
            
            fecha_extraccion_val = None
            if pd.notna(row.get('fecha_extraccion')) and str(row.get('fecha_extraccion', '')).strip() != '':
                try:
                    fecha_extraccion_val = pd.to_datetime(row['fecha_extraccion'])
                except:
                    fecha_extraccion_val = None
            
            created_at_val = None
            if pd.notna(row.get('created_at')) and str(row.get('created_at', '')).strip() != '':
                try:
                    created_at_val = pd.to_datetime(row['created_at'])
                except:
                    created_at_val = None
            
            data_tuples.append((
                str(row.get('titulo', '')),
                fecha_val,
                hora_val,
                float(row['anio']) if pd.notna(row.get('anio')) and str(row.get('anio', '')).strip() != '' else None,
                float(row['mes']) if pd.notna(row.get('mes')) and str(row.get('mes', '')).strip() != '' else None,
                float(row['dia']) if pd.notna(row.get('dia')) and str(row.get('dia', '')).strip() != '' else None,
                str(row.get('dia_semana', '')) if pd.notna(row.get('dia_semana')) else None,
                str(row.get('resumen', '')) if pd.notna(row.get('resumen')) else None,
                str(row.get('contenido', '')) if pd.notna(row.get('contenido')) else None,
                str(row.get('categoria', '')) if pd.notna(row.get('categoria')) else None,
                str(row.get('autor', '')) if pd.notna(row.get('autor')) else None,
                str(row.get('keywords', '')) if pd.notna(row.get('keywords')) else None,
                str(row['url']),
                str(row.get('dominio', '')) if pd.notna(row.get('dominio')) else None,
                fecha_extraccion_val,
                str(row.get('imagen_principal', '')) if pd.notna(row.get('imagen_principal')) else None,
                int(row['cantidad_imagenes']) if pd.notna(row.get('cantidad_imagenes')) and str(row.get('cantidad_imagenes', '')).strip() != '' else None,
                bool(row['tiene_imagenes']) if pd.notna(row.get('tiene_imagenes')) and str(row.get('tiene_imagenes', '')).strip() != '' else None,
                str(row.get('fuente', '')),
                int(row['longitud_titulo']) if pd.notna(row.get('longitud_titulo')) and str(row.get('longitud_titulo', '')).strip() != '' else None,
                float(row['longitud_resumen']) if pd.notna(row.get('longitud_resumen')) and str(row.get('longitud_resumen', '')).strip() != '' else None,
                str(row.get('tipo_contenido', '')) if pd.notna(row.get('tipo_contenido')) else None,
                created_at_val
            ))
        
        # Insertar en lotes
        batch_size = 100
        total_processed = 0
        total_inserted = 0
        total_skipped = 0
        
        for i in range(0, len(data_tuples), batch_size):
            batch = data_tuples[i:i + batch_size]
            try:
                cursor.executemany(insert_query, batch)
                conn.commit()
                # Contar cuántos se insertaron realmente
                inserted_in_batch = cursor.rowcount
                total_inserted += inserted_in_batch
                total_skipped += len(batch) - inserted_in_batch
                total_processed += len(batch)
                print(f"📝 Procesados {total_processed}/{len(data_tuples)} registros... (Insertados: {total_inserted}, Omitidos (duplicados): {total_skipped})")
            except Exception as e:
                print(f"⚠️  Error en lote {i//batch_size + 1}: {e}")
                conn.rollback()
                # Intentar insertar uno por uno para identificar el problema
                for j, record in enumerate(batch):
                    try:
                        cursor.execute(insert_query, record)
                        conn.commit()
                        total_inserted += 1
                    except Exception as e2:
                        # Probablemente duplicado, continuar
                        total_skipped += 1
                        conn.rollback()
        
        # Verificar
        cursor.execute("SELECT COUNT(*) FROM noticias_limpia")
        total_count = cursor.fetchone()[0]
        new_records = total_count - count_before
        
        cursor.execute("""
            SELECT fuente, COUNT(*) as cantidad 
            FROM noticias_limpia 
            GROUP BY fuente 
            ORDER BY cantidad DESC
        """)
        fuentes = cursor.fetchall()
        
        print(f"\n✅ Proceso completado:")
        print(f"   📊 Registros antes: {count_before}")
        print(f"   ➕ Registros nuevos insertados: {new_records}")
        print(f"   ⏭️  Registros omitidos (duplicados por URL): {total_skipped}")
        print(f"   📊 Total en noticias_limpia: {total_count}")
        print(f"\n📰 Distribución por fuente:")
        for fuente, cantidad in fuentes:
            print(f"   - {fuente}: {cantidad}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 MIGRACIÓN COMPLETA: noticias → noticias_limpia")
    print("=" * 60)
    
    # Paso 1: Exportar
    csv_file = export_noticias_to_csv()
    if not csv_file:
        print("❌ Error en la exportación. Abortando.")
        return False
    
    # Paso 2: Normalizar
    normalized_file = normalize_data(csv_file)
    if not normalized_file:
        print("❌ Error en la normalización. Abortando.")
        return False
    
    # Paso 3: Crear tabla y cargar
    success = create_and_load_clean_table(normalized_file)
    if not success:
        print("❌ Error cargando datos. Abortando.")
        return False
    
    print("\n" + "=" * 60)
    print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print(f"📁 Archivos generados:")
    print(f"   - {csv_file}")
    print(f"   - {normalized_file}")
    print(f"\n🎉 Los datos están ahora en la tabla 'noticias_limpia'")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Proceso cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

