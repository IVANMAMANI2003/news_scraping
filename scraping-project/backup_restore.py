#!/usr/bin/env python3
"""
Script para hacer backup y restaurar datos de PostgreSQL
"""

import os
import subprocess
import sys
from datetime import datetime


def backup_database():
    """Hacer backup de la base de datos"""
    print("💾 CREANDO BACKUP DE LA BASE DE DATOS")
    print("=" * 50)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_noticias_{timestamp}.sql"
    
    try:
        # Comando para hacer backup
        cmd = [
            'docker', 'exec', 'news_postgres_prod',
            'pg_dump', '-U', 'postgres', '-d', 'noticias', '--clean', '--create'
        ]
        
        print(f"🔄 Creando backup: {backup_file}")
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"✅ Backup creado exitosamente: {backup_file}")
            return backup_file
        else:
            print(f"❌ Error creando backup: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def restore_to_local(backup_file):
    """Restaurar backup a PostgreSQL local"""
    print(f"\n🔄 RESTAURANDO A POSTGRESQL LOCAL")
    print("=" * 50)
    
    if not os.path.exists(backup_file):
        print(f"❌ Archivo de backup no encontrado: {backup_file}")
        return False
    
    try:
        # Comando para restaurar
        cmd = [
            'psql', '-U', 'postgres', '-h', 'localhost', '-p', '5432', '-f', backup_file
        ]
        
        print(f"🔄 Restaurando desde: {backup_file}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Restauración exitosa")
            return True
        else:
            print(f"❌ Error en restauración: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def show_database_stats():
    """Mostrar estadísticas de la base de datos"""
    print(f"\n📊 ESTADÍSTICAS DE LA BASE DE DATOS")
    print("=" * 50)
    
    try:
        # Conectar a la base de datos Docker
        cmd = [
            'docker', 'exec', 'news_postgres_prod',
            'psql', '-U', 'postgres', '-d', 'noticias', '-c',
            "SELECT fuente, COUNT(*) as total FROM noticias GROUP BY fuente ORDER BY total DESC;"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("📈 Noticias por fuente:")
            print(result.stdout)
        else:
            print(f"❌ Error obteniendo estadísticas: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("🚀 SISTEMA DE BACKUP Y RESTAURACIÓN")
    print("=" * 60)
    print("1. Crear backup de la base de datos Docker")
    print("2. Restaurar a PostgreSQL local")
    print("3. Mostrar estadísticas")
    print("=" * 60)
    
    while True:
        print("\n¿Qué quieres hacer?")
        print("1. Crear backup")
        print("2. Restaurar a local")
        print("3. Ver estadísticas")
        print("4. Salir")
        
        choice = input("\nOpción (1-4): ").strip()
        
        if choice == '1':
            backup_file = backup_database()
            if backup_file:
                print(f"\n✅ Backup guardado como: {backup_file}")
        
        elif choice == '2':
            backup_files = [f for f in os.listdir('.') if f.startswith('backup_noticias_') and f.endswith('.sql')]
            if backup_files:
                print("\nArchivos de backup disponibles:")
                for i, file in enumerate(backup_files, 1):
                    print(f"{i}. {file}")
                
                try:
                    file_choice = int(input("\nSelecciona archivo (número): ")) - 1
                    if 0 <= file_choice < len(backup_files):
                        restore_to_local(backup_files[file_choice])
                    else:
                        print("❌ Opción inválida")
                except ValueError:
                    print("❌ Entrada inválida")
            else:
                print("❌ No hay archivos de backup disponibles")
        
        elif choice == '3':
            show_database_stats()
        
        elif choice == '4':
            print("👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()
