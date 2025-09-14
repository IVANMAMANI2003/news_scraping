#!/usr/bin/env python3
"""
Script para monitorear el progreso de Pachamama Radio
"""

import time
from datetime import datetime, timedelta

import psycopg2

from config.database import get_db_connection


def check_database_status():
    """Verificar estado de la base de datos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Contar total de noticias
        cursor.execute("SELECT COUNT(*) FROM noticias")
        total = cursor.fetchone()[0]
        
        # Contar noticias de Pachamama Radio
        cursor.execute("SELECT COUNT(*) FROM noticias WHERE fuente = 'Pachamama Radio'")
        pachamama_count = cursor.fetchone()[0]
        
        # Últimas noticias de Pachamama
        cursor.execute("""
            SELECT titulo, fecha_extraccion, url 
            FROM noticias 
            WHERE fuente = 'Pachamama Radio' 
            ORDER BY fecha_extraccion DESC 
            LIMIT 3
        """)
        recent = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            'total': total,
            'pachamama': pachamama_count,
            'recent': recent
        }
        
    except Exception as e:
        print(f"❌ Error verificando BD: {e}")
        return None

def monitor_progress():
    """Monitorear progreso cada 30 segundos"""
    print("🔍 MONITOR DE PACHAMAMA RADIO")
    print("=" * 50)
    print("⏰ Iniciando monitoreo...")
    print("📊 Verificando cada 30 segundos")
    print("🛑 Presiona Ctrl+C para detener")
    print("=" * 50)
    
    start_time = datetime.now()
    last_count = 0
    
    try:
        while True:
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            print(f"\n⏰ {current_time.strftime('%H:%M:%S')} (Transcurrido: {elapsed})")
            
            status = check_database_status()
            if status:
                print(f"📊 Total noticias: {status['total']}")
                print(f"📰 Pachamama Radio: {status['pachamama']}")
                
                # Calcular nuevas noticias
                new_articles = status['pachamama'] - last_count
                if new_articles > 0:
                    print(f"🆕 Nuevas noticias: +{new_articles}")
                else:
                    print("⏳ Sin nuevas noticias...")
                
                last_count = status['pachamama']
                
                # Mostrar últimas noticias
                if status['recent']:
                    print("📰 Últimas noticias:")
                    for i, (titulo, fecha, url) in enumerate(status['recent'], 1):
                        print(f"   {i}. {titulo[:50]}... ({fecha})")
                
                # Verificar si han pasado 10 minutos
                if elapsed >= timedelta(minutes=10):
                    print(f"\n🎯 ¡10 minutos completados!")
                    print(f"📊 Total de noticias de Pachamama: {status['pachamama']}")
                    if status['pachamama'] > 0:
                        print("✅ ¡Sistema funcionando correctamente!")
                    else:
                        print("⚠️  No se han extraído noticias aún")
                    break
            else:
                print("❌ Error accediendo a la base de datos")
            
            print("-" * 50)
            time.sleep(30)  # Esperar 30 segundos
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Monitoreo detenido por el usuario")
        print(f"⏰ Tiempo total: {elapsed}")
        if status:
            print(f"📊 Noticias finales de Pachamama: {status['pachamama']}")

if __name__ == "__main__":
    monitor_progress()
