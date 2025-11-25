"""
Router de gestión de usuarios
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth import hash_password, require_role
from ..db import get_conn, put_conn
from ..models import User, UserCreate, UserListResponse, UserUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


def _row_to_user(row: tuple) -> User:
    """Convierte una fila de la base de datos a un objeto User"""
    return User(
        id=row[0],
        email=row[1],
        nombre=row[3],
        apellido=row[4],
        activo=row[5],
        rol=row[6],
        plan=row[7],
        created_at=row[8],
        updated_at=row[9],
        last_login=row[10],
        email_verificado=row[11],
    )


@router.get("", response_model=UserListResponse)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    activo: bool = Query(None),
    rol: str = Query(None),
    plan: str = Query(None),
    current_user: dict = Depends(require_role(["admin"])),
):
    """Lista todos los usuarios (solo admin)"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        where_conditions = []
        params = []
        
        if activo is not None:
            where_conditions.append("activo = %s")
            params.append(activo)
        
        if rol:
            where_conditions.append("rol = %s")
            params.append(rol)
        
        if plan:
            where_conditions.append("plan = %s")
            params.append(plan)
        
        where_sql = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Contar total
        cur.execute(f"SELECT COUNT(*) FROM usuarios {where_sql}", params)
        total = cur.fetchone()[0]
        
        # Obtener usuarios
        cur.execute(
            f"SELECT id, email, password_hash, nombre, apellido, activo, rol, plan, "
            f"created_at, updated_at, last_login, email_verificado "
            f"FROM usuarios {where_sql} "
            f"ORDER BY created_at DESC OFFSET %s LIMIT %s",
            params + [skip, limit]
        )
        rows = cur.fetchall()
        
        items = [_row_to_user(row) for row in rows]
        
        return UserListResponse(total=total, items=items)
    finally:
        put_conn(conn)


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: int,
    current_user: dict = Depends(require_role(["admin", "user", "moderator"])),
):
    """Obtiene un usuario por ID"""
    # Los usuarios solo pueden ver su propia información, los admins pueden ver cualquiera
    if current_user["rol"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este usuario"
        )
    
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, password_hash, nombre, apellido, activo, rol, plan, "
            "created_at, updated_at, last_login, email_verificado "
            "FROM usuarios WHERE id = %s",
            (user_id,)
        )
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return _row_to_user(row)
    finally:
        put_conn(conn)


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_role(["admin"])),
):
    """Crea un nuevo usuario (solo admin)"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Verificar si el email ya existe
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (user_data.email,))
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Hashear contraseña
        password_hash = hash_password(user_data.password)
        
        # Insertar usuario
        cur.execute(
            "INSERT INTO usuarios (email, password_hash, nombre, apellido, plan) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id, email, password_hash, nombre, apellido, activo, rol, plan, created_at, updated_at, last_login, email_verificado",
            (user_data.email, password_hash, user_data.nombre, user_data.apellido, user_data.plan)
        )
        row = cur.fetchone()
        conn.commit()
        
        return _row_to_user(row)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario: {str(e)}"
        )
    finally:
        put_conn(conn)


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: dict = Depends(require_role(["admin", "user", "moderator"])),
):
    """Actualiza un usuario"""
    # Los usuarios solo pueden actualizar su propia información (excepto rol y plan), los admins pueden actualizar cualquiera
    if current_user["rol"] != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar este usuario"
        )
    
    # Los usuarios no pueden cambiar su rol o plan
    if current_user["rol"] != "admin":
        user_data.rol = None
        user_data.plan = None
    
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Verificar que el usuario existe
        cur.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
        if not cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Construir query de actualización
        updates = []
        params = []
        
        if user_data.email is not None:
            # Verificar que el email no esté en uso por otro usuario
            cur.execute("SELECT id FROM usuarios WHERE email = %s AND id != %s", (user_data.email, user_id))
            if cur.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está en uso"
                )
            updates.append("email = %s")
            params.append(user_data.email)
        
        if user_data.nombre is not None:
            updates.append("nombre = %s")
            params.append(user_data.nombre)
        
        if user_data.apellido is not None:
            updates.append("apellido = %s")
            params.append(user_data.apellido)
        
        if user_data.activo is not None and current_user["rol"] == "admin":
            updates.append("activo = %s")
            params.append(user_data.activo)
        
        if user_data.rol is not None and current_user["rol"] == "admin":
            updates.append("rol = %s")
            params.append(user_data.rol)
        
        if user_data.plan is not None and current_user["rol"] == "admin":
            updates.append("plan = %s")
            params.append(user_data.plan)
        
        if user_data.password is not None:
            password_hash = hash_password(user_data.password)
            updates.append("password_hash = %s")
            params.append(password_hash)
        
        if not updates:
            # Si no hay cambios, obtener y retornar el usuario actual
            cur.execute(
                "SELECT id, email, password_hash, nombre, apellido, activo, rol, plan, "
                "created_at, updated_at, last_login, email_verificado "
                "FROM usuarios WHERE id = %s",
                (user_id,)
            )
            return _row_to_user(cur.fetchone())
        
        params.append(user_id)
        cur.execute(
            f"UPDATE usuarios SET {', '.join(updates)} WHERE id = %s "
            "RETURNING id, email, password_hash, nombre, apellido, activo, rol, plan, "
            "created_at, updated_at, last_login, email_verificado",
            params
        )
        row = cur.fetchone()
        
        # Si se actualizó el plan, sincronizar con todas las API keys del usuario
        if user_data.plan is not None and current_user["rol"] == "admin":
            cur.execute(
                "UPDATE api_keys SET plan = %s WHERE usuario_id = %s",
                (user_data.plan, user_id)
            )
            logger.info(f"✅ Plan sincronizado: Usuario {user_id} -> Plan {user_data.plan} -> Todas sus API keys actualizadas")
        
        conn.commit()
        
        return _row_to_user(row)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar usuario: {str(e)}"
        )
    finally:
        put_conn(conn)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: dict = Depends(require_role(["admin"])),
):
    """Elimina un usuario (solo admin)"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Verificar que el usuario existe
        cur.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
        if not cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # No permitir eliminar el propio usuario
        if current_user["id"] == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes eliminar tu propio usuario"
            )
        
        cur.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))
        conn.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar usuario: {str(e)}"
        )
    finally:
        put_conn(conn)

