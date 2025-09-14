#!/usr/bin/env python3
"""
Script para controlar tareas de Celery
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_app import celery_app


def list_active_tasks():
    """Listar tareas activas"""
    print("📋 Tareas activas:")
    print("=" * 50)
    
    active = celery_app.control.inspect().active()
    
    if active:
        for worker, tasks in active.items():
            print(f"🔧 Worker: {worker}")
            for task in tasks:
                print(f"   - {task['name']} (ID: {task['id']})")
                print(f"     Args: {task['args']}")
                print(f"     Tiempo: {task['time_start']}")
    else:
        print("ℹ️ No hay tareas activas")

def list_scheduled_tasks():
    """Listar tareas programadas"""
    print("⏰ Tareas programadas:")
    print("=" * 50)
    
    scheduled = celery_app.control.inspect().scheduled()
    
    if scheduled:
        for worker, tasks in scheduled.items():
            print(f"🔧 Worker: {worker}")
            for task in tasks:
                print(f"   - {task['request']['name']} (ID: {task['request']['id']})")
                print(f"     ETA: {task['eta']}")
    else:
        print("ℹ️ No hay tareas programadas")

def list_queues():
    """Listar colas y estadísticas"""
    print("📊 Estado de colas:")
    print("=" * 50)
    
    inspect = celery_app.control.inspect()
    
    # Estadísticas de workers
    stats = inspect.stats()
    if stats:
        for worker, stat in stats.items():
            print(f"🔧 Worker: {worker}")
            print(f"   - Pool: {stat.get('pool', {}).get('max-concurrency', 'N/A')}")
            print(f"   - Tareas procesadas: {stat.get('total', {}).get('celery_tasks.scraping_tasks.scrape_all_sources', 0)}")
    
    # Tareas activas por cola
    active = inspect.active()
    if active:
        print(f"\n📋 Tareas activas: {sum(len(tasks) for tasks in active.values())}")
    
    # Tareas programadas
    scheduled = inspect.scheduled()
    if scheduled:
        print(f"⏰ Tareas programadas: {sum(len(tasks) for tasks in scheduled.values())}")

def trigger_scraping():
    """Disparar scraping inmediato"""
    print("🚀 Disparando scraping inmediato...")
    
    try:
        result = celery_app.send_task('scrape_all_sources')
        print(f"✅ Tarea enviada. ID: {result.id}")
        print(f"📊 Estado: {result.status}")
        
        return result.id
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def trigger_migration():
    """Disparar migración inmediata"""
    print("🗄️ Disparando migración inmediata...")
    
    try:
        result = celery_app.send_task('migrate_all_sources')
        print(f"✅ Tarea enviada. ID: {result.id}")
        print(f"📊 Estado: {result.status}")
        
        return result.id
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def trigger_cleanup():
    """Disparar limpieza inmediata"""
    print("🧹 Disparando limpieza inmediata...")
    
    try:
        result = celery_app.send_task('cleanup_old_data')
        print(f"✅ Tarea enviada. ID: {result.id}")
        print(f"📊 Estado: {result.status}")
        
        return result.id
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_task_result(task_id):
    """Obtener resultado de una tarea"""
    print(f"📊 Resultado de tarea {task_id}:")
    print("=" * 50)
    
    try:
        result = celery_app.AsyncResult(task_id)
        
        print(f"Estado: {result.status}")
        print(f"Listo: {result.ready()}")
        print(f"Exitoso: {result.successful()}")
        print(f"Falló: {result.failed()}")
        
        if result.ready():
            if result.successful():
                print(f"Resultado: {result.result}")
            else:
                print(f"Error: {result.result}")
        else:
            print("Tarea aún en progreso...")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def purge_queues():
    """Limpiar todas las colas"""
    print("🧹 Limpiando colas...")
    
    try:
        celery_app.control.purge()
        print("✅ Colas limpiadas")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Controlar tareas de Celery')
    parser.add_argument('action', 
                       choices=['list-active', 'list-scheduled', 'list-queues', 
                               'trigger-scraping', 'trigger-migration', 'trigger-cleanup',
                               'get-result', 'purge'],
                       help='Acción a realizar')
    parser.add_argument('--task-id', help='ID de tarea (para get-result)')
    
    args = parser.parse_args()
    
    if args.action == 'list-active':
        list_active_tasks()
    elif args.action == 'list-scheduled':
        list_scheduled_tasks()
    elif args.action == 'list-queues':
        list_queues()
    elif args.action == 'trigger-scraping':
        trigger_scraping()
    elif args.action == 'trigger-migration':
        trigger_migration()
    elif args.action == 'trigger-cleanup':
        trigger_cleanup()
    elif args.action == 'get-result':
        if args.task_id:
            get_task_result(args.task_id)
        else:
            print("❌ Se requiere --task-id para get-result")
    elif args.action == 'purge':
        purge_queues()

if __name__ == '__main__':
    main()
