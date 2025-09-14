#!/usr/bin/env python3
"""
Verificar el estado del sistema automático
"""

import time
from datetime import datetime

from config.database import get_db_connection


def check_system_status():
    """Verificar estado del sistema"""
    print("🔍 VERIFICANDO SISTEMA AUTOMÁTICO")
    print("=" * 50)
    print(f"⏰ Verificación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Verificar base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Contar total de noticias
        cursor.execute("SELECT COUNT(*) FROM noticias")
        total = cursor.fetchone()[0]
        print(f"📊 Total de noticias en BD: {total}")
        
        # Contar por fuente
        cursor.execute("SELECT fuente, COUNT(*) FROM noticias GROUP BY fuente ORDER BY COUNT(*) DESC")
        sources = cursor.fetchall()
        
        print(f"\n📈 Noticias por fuente:")
        for fuente, count in sources:
            print(f"   {fuente}: {count}")
        
        # Últimas noticias
        cursor.execute("""
            SELECT titulo, fecha_extraccion, fuente 
            FROM noticias 
            ORDER BY fecha_extraccion DESC 
            LIMIT 5
        """)
        recent = cursor.fetchall()
        
        print(f"\n🆕 Últimas noticias:")
        for i, (titulo, fecha, fuente) in enumerate(recent, 1):
            print(f"   {i}. {titulo[:50]}... ({fuente}) - {fecha}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando BD: {e}")
        return False

def monitor_automatic_system():
    """Monitorear el sistema automático"""
    print("🚀 MONITOR DEL SISTEMA AUTOMÁTICO")
    print("=" * 60)
    print("⏰ El sistema se ejecuta automáticamente cada 6 horas")
    print("📊 Verificando cada 30 segundos...")
    print("🛑 Presiona Ctrl+C para detener")
    print("=" * 60)
    
    last_count = 0
    
    try:
        while True:
            current_time = datetime.now()
            print(f"\n⏰ {current_time.strftime('%H:%M:%S')}")
            
            if check_system_status():
                # Verificar si hay nuevas noticias
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM noticias")
                current_count = cursor.fetchone()[0]
                cursor.close()
                conn.close()
                
                new_articles = current_count - last_count
                if new_articles > 0:
                    print(f"🆕 ¡Nuevas noticias! +{new_articles}")
                else:
                    print("⏳ Sin nuevas noticias...")
                
                last_count = current_count
            
            print("-" * 50)
            time.sleep(30)  # Esperar 30 segundos
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Monitor detenido por el usuario")

if __name__ == "__main__":
    monitor_automatic_system()
