#!/usr/bin/env python3
"""
Instalación rápida de dependencias esenciales
"""

import subprocess
import sys


def install_package(package):
    """Instala un paquete usando pip"""
    try:
        print(f"📦 Instalando {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} instalado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al instalar {package}: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Instalación Rápida de Dependencias")
    print("=" * 50)
    
    # Dependencias esenciales
    packages = [
        "scrapy",
        "psycopg2-binary",
        "python-dotenv",
        "schedule"
    ]
    
    successful = 0
    failed = 0
    
    for package in packages:
        if install_package(package):
            successful += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Resumen de instalación:")
    print(f"✅ Exitosos: {successful}")
    print(f"❌ Fallidos: {failed}")
    
    if failed == 0:
        print("\n🎉 ¡Todas las dependencias instaladas!")
        print("✅ Ahora puedes ejecutar: python test_spiders_simple.py")
    else:
        print(f"\n⚠️  {failed} paquetes fallaron")
        print("Revisa los errores arriba")

if __name__ == "__main__":
    main()
