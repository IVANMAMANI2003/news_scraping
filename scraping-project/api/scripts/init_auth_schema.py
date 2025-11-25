"""
Script para inicializar el esquema de autenticación en la base de datos
"""
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth import hash_password
from api.db import get_conn, put_conn


def init_schema():
    """Ejecuta el script SQL para crear las tablas de autenticación"""
    schema_file = os.path.join(os.path.dirname(__file__), "..", "schemas", "auth.sql")
    
    if not os.path.exists(schema_file):
        print(f"❌ Error: No se encontró el archivo {schema_file}")
        return False
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    conn = get_conn()
    try:
        cur = conn.cursor()
        # Ejecutar el SQL completo usando execute() que puede manejar múltiples statements
        # psycopg2 puede ejecutar múltiples statements si están separados por punto y coma
        try:
            cur.execute(sql)
            conn.commit()
            
            # Asegurar que el usuario admin existe con un hash válido
            cur.execute("SELECT id, password_hash FROM usuarios WHERE email = 'admin@biznews.com'")
            admin_data = cur.fetchone()
            
            if not admin_data:
                print("⚠️  Usuario admin no encontrado. Creándolo...")
                admin_hash = hash_password("admin123")
                cur.execute(
                    "INSERT INTO usuarios (email, password_hash, nombre, apellido, rol, plan, activo, email_verificado) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (email) DO NOTHING",
                    ("admin@biznews.com", admin_hash, "Admin", "Sistema", "admin", "enterprise", True, True)
                )
                conn.commit()
                print("✅ Usuario admin creado")
            else:
                # Verificar y actualizar el hash si es necesario
                current_hash = admin_data[1]
                if not current_hash or len(current_hash) < 50 or not current_hash.startswith("$2b$"):
                    print("⚠️  Hash del admin inválido. Actualizándolo...")
                    admin_hash = hash_password("admin123")
                    cur.execute(
                        "UPDATE usuarios SET password_hash = %s WHERE email = 'admin@biznews.com'",
                        (admin_hash,)
                    )
                    conn.commit()
                    print("✅ Hash del admin actualizado")
            
            print("✅ Esquema de autenticación inicializado correctamente")
            return True
        except Exception as e:
            # Si hay errores de "ya existe", intentar ejecutar statement por statement
            error_msg = str(e).lower()
            if 'already exists' in error_msg or 'ya existe' in error_msg:
                print("⚠️  Algunos objetos ya existen. Ejecutando statements individualmente...")
                conn.rollback()
                
                # Usar execute_batch o ejecutar manualmente
                # Dividir por punto y coma pero mantener funciones completas
                import re

                # Patrón para encontrar funciones completas
                function_pattern = r'CREATE\s+(OR\s+REPLACE\s+)?FUNCTION.*?\$\$[^$]*\$\$'
                
                # Separar funciones del resto
                functions = re.findall(function_pattern, sql, re.DOTALL | re.IGNORECASE)
                rest_sql = sql
                for func in functions:
                    rest_sql = rest_sql.replace(func, '')
                
                # Ejecutar funciones primero
                for func in functions:
                    try:
                        cur.execute(func)
                    except Exception as func_err:
                        func_err_msg = str(func_err).lower()
                        if 'already exists' in func_err_msg or 'ya existe' in func_err_msg:
                            print(f"⚠️  Función ya existe, omitiendo...")
                            continue
                        else:
                            print(f"⚠️  Error en función: {str(func_err)[:100]}")
                
                # Ejecutar el resto del SQL statement por statement
                statements = [s.strip() for s in rest_sql.split(';') if s.strip() and not s.strip().startswith('--')]
                for statement in statements:
                    if not statement:
                        continue
                    try:
                        cur.execute(statement)
                    except Exception as stmt_err:
                        stmt_err_msg = str(stmt_err).lower()
                        if 'already exists' in stmt_err_msg or 'ya existe' in stmt_err_msg or 'duplicate' in stmt_err_msg:
                            # Ignorar errores de objetos que ya existen
                            continue
                        else:
                            print(f"⚠️  Advertencia: {str(stmt_err)[:150]}")
                
                conn.commit()
                
                # Asegurar que el usuario admin existe con un hash válido
                cur.execute("SELECT id FROM usuarios WHERE email = 'admin@biznews.com'")
                admin_exists = cur.fetchone()
                
                if not admin_exists:
                    print("⚠️  Usuario admin no encontrado. Creándolo...")
                    admin_hash = hash_password("admin123")
                    cur.execute(
                        "INSERT INTO usuarios (email, password_hash, nombre, apellido, rol, plan, activo, email_verificado) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (email) DO NOTHING",
                        ("admin@biznews.com", admin_hash, "Admin", "Sistema", "admin", "enterprise", True, True)
                    )
                    conn.commit()
                    print("✅ Usuario admin creado")
                else:
                    # Verificar y actualizar el hash si es necesario
                    cur.execute("SELECT password_hash FROM usuarios WHERE email = 'admin@biznews.com'")
                    current_hash = cur.fetchone()[0]
                    # Si el hash parece inválido (muy corto o no empieza con $2b$), actualizarlo
                    if not current_hash or len(current_hash) < 50 or not current_hash.startswith("$2b$"):
                        print("⚠️  Hash del admin inválido. Actualizándolo...")
                        admin_hash = hash_password("admin123")
                        cur.execute(
                            "UPDATE usuarios SET password_hash = %s WHERE email = 'admin@biznews.com'",
                            (admin_hash,)
                        )
                        conn.commit()
                        print("✅ Hash del admin actualizado")
                
                print("✅ Esquema de autenticación inicializado (con algunas advertencias)")
                return True
            else:
                raise
    except Exception as e:
        conn.rollback()
        print(f"❌ Error al inicializar esquema: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        put_conn(conn)


if __name__ == "__main__":
    print("🚀 Inicializando esquema de autenticación...")
    success = init_schema()
    sys.exit(0 if success else 1)

