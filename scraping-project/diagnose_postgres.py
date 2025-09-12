#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de conexión a PostgreSQL
"""

import socket
import sys
from datetime import datetime

import psycopg2


def test_postgres_connection():
    """Prueba la conexión a PostgreSQL con diferentes configuraciones"""
    
    # Diferentes configuraciones para probar
    configs = [
        {
            'name': 'Configuración 1 (localhost)',
            'host': 'localhost',
            'database': 'noticias',
            'user': 'postgres',
            'password': '123456',
            'port': '5432'
        },
        {
            'name': 'Configuración 2 (127.0.0.1)',
            'host': '127.0.0.1',
            'database': 'noticias',
            'user': 'postgres',
            'password': '123456',
            'port': '5432'
        },
        {
            'name': 'Configuración 3 (usuario root)',
            'host': '127.0.0.1',
            'database': 'noticias',
            'user': 'root',
            'password': '123456',
            'port': '5432'
        },
        {
            'name': 'Configuración 4 (puerto 5433)',
            'host': '127.0.0.1',
            'database': 'noticias',
            'user': 'postgres',
            'password': '123456',
            'port': '5433'
        }
    ]
    
    print("🔍 Diagnóstico de conexión a PostgreSQL")
    print("=" * 60)
    
    for config in configs:
        print(f"\n📋 Probando: {config['name']}")
        print(f"   Host: {config['host']}")
        print(f"   Database: {config['database']}")
        print(f"   User: {config['user']}")
        print(f"   Port: {config['port']}")
        
        try:
            # Probar conexión
            conn = psycopg2.connect(
                host=config['host'],
                database=config['database'],
                user=config['user'],
                password=config['password'],
                port=config['port'],
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            print(f"   ✅ ¡CONEXIÓN EXITOSA!")
            print(f"   📊 Versión: {version[0][:50]}...")
            
            # Probar si la tabla existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'noticias'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                print(f"   📋 Tabla 'noticias': ✅ Existe")
                
                # Contar registros
                cursor.execute("SELECT COUNT(*) FROM noticias;")
                count = cursor.fetchone()[0]
                print(f"   📊 Registros en tabla: {count}")
            else:
                print(f"   📋 Tabla 'noticias': ❌ No existe")
            
            cursor.close()
            conn.close()
            
            # Si llegamos aquí, la conexión funcionó
            print(f"\n🎉 ¡CONFIGURACIÓN EXITOSA ENCONTRADA!")
            print(f"   Usa esta configuración en tus archivos:")
            print(f"   Host: {config['host']}")
            print(f"   Database: {config['database']}")
            print(f"   User: {config['user']}")
            print(f"   Port: {config['port']}")
            return config
            
        except psycopg2.OperationalError as e:
            print(f"   ❌ Error de conexión: {str(e)}")
        except psycopg2.Error as e:
            print(f"   ❌ Error de PostgreSQL: {str(e)}")
        except Exception as e:
            print(f"   ❌ Error inesperado: {str(e)}")
    
    return None

def test_network_connectivity():
    """Prueba la conectividad de red"""
    print(f"\n🌐 Probando conectividad de red...")
    
    hosts_to_test = [
        ('localhost', 5432),
        ('127.0.0.1', 5432),
        ('127.0.0.1', 5433)
    ]
    
    for host, port in hosts_to_test:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"   ✅ {host}:{port} - Puerto abierto")
            else:
                print(f"   ❌ {host}:{port} - Puerto cerrado o no disponible")
        except Exception as e:
            print(f"   ❌ {host}:{port} - Error: {str(e)}")

def check_postgres_process():
    """Verifica si PostgreSQL está ejecutándose"""
    print(f"\n🔍 Verificando proceso de PostgreSQL...")
    
    try:
        import subprocess

        # En Windows
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq postgres.exe'], 
                              capture_output=True, text=True)
        
        if 'postgres.exe' in result.stdout:
            print("   ✅ PostgreSQL está ejecutándose")
            return True
        else:
            print("   ❌ PostgreSQL no está ejecutándose")
            print("   💡 Inicia PostgreSQL desde el menú de inicio o servicios")
            return False
            
    except Exception as e:
        print(f"   ⚠️  No se pudo verificar el proceso: {str(e)}")
        return False

def main():
    """Función principal de diagnóstico"""
    print("🔧 Diagnóstico de PostgreSQL para el proyecto de scraping")
    print("=" * 70)
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Verificar proceso
    postgres_running = check_postgres_process()
    
    # 2. Verificar conectividad de red
    test_network_connectivity()
    
    # 3. Probar conexiones
    working_config = test_postgres_connection()
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 70)
    
    if working_config:
        print("✅ ¡PostgreSQL está funcionando correctamente!")
        print(f"📋 Configuración que funciona:")
        print(f"   Host: {working_config['host']}")
        print(f"   Database: {working_config['database']}")
        print(f"   User: {working_config['user']}")
        print(f"   Port: {working_config['port']}")
        
        print(f"\n📝 Próximos pasos:")
        print(f"1. Actualiza los archivos de configuración con estos valores")
        print(f"2. Ejecuta: python setup_database.py")
        print(f"3. Prueba el scraping: scrapy crawl test")
        
    else:
        print("❌ No se pudo conectar a PostgreSQL")
        print(f"\n💡 Soluciones sugeridas:")
        print(f"1. Verifica que PostgreSQL esté instalado y ejecutándose")
        print(f"2. Verifica que la base de datos 'noticias' exista")
        print(f"3. Verifica las credenciales (usuario/contraseña)")
        print(f"4. Verifica que el puerto 5432 esté abierto")
        print(f"5. Intenta crear la base de datos manualmente:")
        print(f"   - Abre pgAdmin o psql")
        print(f"   - Crea la base de datos 'noticias'")
        print(f"   - Verifica los permisos del usuario")

if __name__ == "__main__":
    main()
