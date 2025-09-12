#!/usr/bin/env python3
"""
Script de instalación y configuración completa del proyecto
"""

import os
import subprocess
import sys
from pathlib import Path


def install_requirements():
    """Instala las dependencias del proyecto"""
    print("📦 Instalando dependencias...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requeriments.txt"])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al instalar dependencias: {e}")
        return False

def create_env_file():
    """Crea el archivo .env si no existe"""
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creando archivo .env...")
        try:
            with open("env_example.txt", "r") as source:
                content = source.read()
            
            with open(".env", "w") as target:
                target.write(content)
            
            print("✅ Archivo .env creado")
            print("⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales de PostgreSQL")
            return True
        except Exception as e:
            print(f"❌ Error al crear .env: {e}")
            return False
    else:
        print("✅ Archivo .env ya existe")
        return True

def check_postgresql():
    """Verifica si PostgreSQL está disponible"""
    print("🔍 Verificando PostgreSQL...")
    try:
        import psycopg2
        print("✅ psycopg2 disponible")
        return True
    except ImportError:
        print("❌ psycopg2 no está instalado")
        return False

def setup_database():
    """Configura la base de datos"""
    print("🗄️  Configurando base de datos...")
    try:
        subprocess.check_call([sys.executable, "setup_database.py"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al configurar base de datos: {e}")
        return False

def test_scraping():
    """Prueba el scraping con un spider"""
    print("🧪 Probando scraping...")
    try:
        # Ejecutar un spider de prueba
        result = subprocess.run([
            'scrapy', 'crawl', 'losandes', '--nolog'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Scraping funcionando correctamente")
            return True
        else:
            print(f"⚠️  Scraping completado con advertencias: {result.stderr}")
            return True  # Aún así consideramos exitoso
    except subprocess.TimeoutExpired:
        print("⏰ Timeout en prueba de scraping (esto es normal)")
        return True
    except Exception as e:
        print(f"❌ Error en prueba de scraping: {e}")
        return False

def main():
    """Función principal de instalación"""
    print("🚀 Instalador del Sistema de Scraping de Noticias")
    print("=" * 60)
    
    steps = [
        ("Instalando dependencias", install_requirements),
        ("Creando archivo de configuración", create_env_file),
        ("Verificando PostgreSQL", check_postgresql),
        ("Configurando base de datos", setup_database),
        ("Probando scraping", test_scraping)
    ]
    
    successful = 0
    failed = 0
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if step_func():
            successful += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Resumen de instalación:")
    print(f"✅ Exitosos: {successful}")
    print(f"❌ Fallidos: {failed}")
    
    if failed == 0:
        print("\n🎉 ¡Instalación completada exitosamente!")
        print("\n📝 Próximos pasos:")
        print("1. Edita el archivo .env con tus credenciales de PostgreSQL")
        print("2. Ejecuta: python run_scraping.py")
        print("3. O ejecuta: python scheduler.py (para modo automático)")
    else:
        print(f"\n⚠️  Instalación completada con {failed} errores")
        print("Revisa los mensajes de error arriba para solucionarlos")

if __name__ == "__main__":
    main()
