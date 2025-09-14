#!/usr/bin/env python3
"""
Script para iniciar workers de Celery
"""

import argparse
import os
import sys

from celery import Celery

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery_app import celery_app


def start_worker(queue='scraping', concurrency=4, loglevel='info'):
    """
    Iniciar un worker de Celery
    """
    print(f"🚀 Iniciando worker de Celery")
    print(f"📋 Cola: {queue}")
    print(f"⚡ Concurrencia: {concurrency}")
    print(f"📝 Nivel de log: {loglevel}")
    print("=" * 50)
    
    # Configurar worker
    worker = celery_app.Worker(
        queues=[queue],
        concurrency=concurrency,
        loglevel=loglevel,
        hostname=f'worker-{queue}@%h'
    )
    
    # Iniciar worker
    worker.start()

def main():
    parser = argparse.ArgumentParser(description='Iniciar worker de Celery')
    parser.add_argument('--queue', default='scraping', 
                       choices=['scraping', 'migration', 'cleanup'],
                       help='Cola a procesar')
    parser.add_argument('--concurrency', type=int, default=4,
                       help='Número de procesos concurrentes')
    parser.add_argument('--loglevel', default='info',
                       choices=['debug', 'info', 'warning', 'error'],
                       help='Nivel de logging')
    
    args = parser.parse_args()
    
    start_worker(
        queue=args.queue,
        concurrency=args.concurrency,
        loglevel=args.loglevel
    )

if __name__ == '__main__':
    main()
