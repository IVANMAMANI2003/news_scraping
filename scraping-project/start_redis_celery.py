#!/usr/bin/env python3
"""
Script para iniciar Redis y Celery de forma automatizada
"""

import os
import signal
import subprocess
import sys
import time
from datetime import datetime


def check_redis_running():
    """Verificar si Redis está ejecutándose"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except:
        return False

def start_redis():
    """Iniciar Redis"""
    print("🔴 Iniciando Redis...")
    
    if check_redis_running():
        print("✅ Redis ya está ejecutándose")
        return True
    
    try:
        # Intentar iniciar Redis
        if os.name == 'nt':  # Windows
            subprocess.Popen(['redis-server'], shell=True)
        else:  # Linux/Mac
            subprocess.Popen(['redis-server'])
        
        # Esperar a que Redis inicie
        for i in range(10):
            time.sleep(1)
            if check_redis_running():
                print("✅ Redis iniciado correctamente")
                return True
        
        print("❌ No se pudo iniciar Redis")
        return False
        
    except Exception as e:
        print(f"❌ Error iniciando Redis: {e}")
        return False

def start_celery_worker(queue='scraping'):
    """Iniciar worker de Celery"""
    print(f"🔧 Iniciando worker de Celery (cola: {queue})...")
    
    try:
        cmd = [sys.executable, 'celery_workers/start_worker.py', '--queue', queue]
        process = subprocess.Popen(cmd)
        return process
    except Exception as e:
        print(f"❌ Error iniciando worker: {e}")
        return None

def start_celery_beat():
    """Iniciar scheduler de Celery Beat"""
    print("⏰ Iniciando Celery Beat...")
    
    try:
        cmd = [sys.executable, 'celery_workers/start_beat.py']
        process = subprocess.Popen(cmd)
        return process
    except Exception as e:
        print(f"❌ Error iniciando Beat: {e}")
        return None

def main():
    print("🚀 INICIADOR DE REDIS Y CELERY")
    print("=" * 50)
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    processes = []
    
    try:
        # 1. Iniciar Redis
        if not start_redis():
            print("❌ No se puede continuar sin Redis")
            return
        
        # 2. Iniciar workers de Celery
        worker_processes = []
        for queue in ['scraping', 'migration', 'cleanup']:
            process = start_celery_worker(queue)
            if process:
                worker_processes.append(process)
                processes.append(process)
        
        # 3. Iniciar Celery Beat
        beat_process = start_celery_beat()
        if beat_process:
            processes.append(beat_process)
        
        print("\n✅ Todos los servicios iniciados")
        print("📋 Procesos activos:")
        for i, process in enumerate(processes):
            print(f"   {i+1}. PID: {process.pid}")
        
        print("\n🎯 Comandos útiles:")
        print("   - Ver tareas: python celery_workers/control_tasks.py list-queues")
        print("   - Disparar scraping: python celery_workers/control_tasks.py trigger-scraping")
        print("   - Ver resultado: python celery_workers/control_tasks.py get-result --task-id <ID>")
        
        print("\n⏹️  Presiona Ctrl+C para detener todos los servicios")
        
        # Mantener el script ejecutándose
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicios...")
        
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        
        print("✅ Servicios detenidos")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Limpiar procesos
        for process in processes:
            try:
                process.terminate()
            except:
                pass

if __name__ == '__main__':
    main()
