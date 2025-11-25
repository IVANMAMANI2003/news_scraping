"""
Script para actualizar la contraseña del usuario admin
"""
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth import hash_password
from api.db import get_conn, put_conn


def fix_admin_password():
    """Actualiza la contraseña del usuario admin con un hash válido"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Generar nuevo hash para "admin123"
        new_hash = hash_password("admin123")
        print(f"🔑 Nuevo hash generado: {new_hash}")
        
        # Actualizar el hash en la base de datos
        cur.execute(
            "UPDATE usuarios SET password_hash = %s WHERE email = %s",
            (new_hash, "admin@biznews.com")
        )
        
        if cur.rowcount > 0:
            conn.commit()
            print("✅ Contraseña del admin actualizada correctamente")
            print("   Email: admin@biznews.com")
            print("   Password: admin123")
            return True
        else:
            print("⚠️  No se encontró el usuario admin")
            return False
    except Exception as e:
        conn.rollback()
        print(f"❌ Error al actualizar contraseña: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        put_conn(conn)


if __name__ == "__main__":
    print("🚀 Actualizando contraseña del usuario admin...")
    success = fix_admin_password()
    sys.exit(0 if success else 1)

