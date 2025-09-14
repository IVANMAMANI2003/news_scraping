#!/usr/bin/env python3
"""
Prueba simple de Pachamama Radio
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pachamama():
    print("🧪 PRUEBA SIMPLE DE PACHAMAMA RADIO")
    print("=" * 50)
    
    try:
        from spiders.pachamamaradio_local import main
        print("✅ Spider importado correctamente")
        
        print("🕷️  Ejecutando scraping...")
        csv_file, json_file = main()
        
        if csv_file and json_file:
            print(f"✅ Archivos generados:")
            print(f"   📄 CSV: {csv_file}")
            print(f"   📄 JSON: {json_file}")
            
            # Verificar que los archivos existen
            if os.path.exists(csv_file):
                print(f"✅ CSV existe: {os.path.getsize(csv_file)} bytes")
            else:
                print("❌ CSV no existe")
                
            if os.path.exists(json_file):
                print(f"✅ JSON existe: {os.path.getsize(json_file)} bytes")
            else:
                print("❌ JSON no existe")
        else:
            print("❌ No se generaron archivos")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pachamama()
