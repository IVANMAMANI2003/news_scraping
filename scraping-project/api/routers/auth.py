"""
Router de autenticación
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from ..auth import (create_access_token, create_refresh_token,
                    get_user_by_email, hash_password, require_role, security,
                    update_last_login, verify_password, verify_token)
from ..db import get_conn, put_conn
from ..models import LoginRequest, LoginResponse, User, UserCreate

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


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate):
    """Registra un nuevo usuario"""
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
            detail=f"Error al registrar usuario: {str(e)}"
        )
    finally:
        put_conn(conn)


@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest):
    """Inicia sesión y retorna tokens"""
    user = get_user_by_email(login_data.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    if not user[5]:  # user[5] es 'activo'
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    if not verify_password(login_data.password, user[2]):  # user[2] es 'password_hash'
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    # Actualizar último login
    update_last_login(user[0])
    
    # Crear tokens
    access_token = create_access_token({"sub": user[0], "email": user[1], "rol": user[6]})
    refresh_token = create_refresh_token({"sub": user[0], "email": user[1]})
    
    # Guardar sesión
    conn = get_conn()
    try:
        cur = conn.cursor()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        cur.execute(
            "INSERT INTO sesiones (usuario_id, token, refresh_token, expires_at) "
            "VALUES (%s, %s, %s, %s)",
            (user[0], access_token, refresh_token, expires_at)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        # No fallar el login si hay error al guardar la sesión
        print(f"⚠️  Error al guardar sesión: {str(e)}")
    finally:
        put_conn(conn)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_row_to_user(user),
        expires_in=3600
    )


@router.post("/refresh", response_model=LoginResponse)
def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Refresca el access token usando el refresh token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido"
        )
    
    user_id = payload.get("sub")
    user = get_user_by_email(payload.get("email"))
    
    if not user or not user[5]:  # Verificar que esté activo
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )
    
    # Crear nuevos tokens
    access_token = create_access_token({"sub": user_id, "email": user[1], "rol": user[6]})
    refresh_token = create_refresh_token({"sub": user_id, "email": user[1]})
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_row_to_user(user),
        expires_in=3600
    )


@router.post("/logout")
def logout(current_user: dict = Depends(require_role(["admin", "user", "moderator"]))):
    """Cierra sesión (invalida el token)"""
    # En una implementación completa, se invalidaría el token en la BD
    # Por ahora, solo retornamos éxito
    return {"message": "Sesión cerrada exitosamente"}


@router.get("/me", response_model=User)
def get_current_user_info(current_user: dict = Depends(require_role(["admin", "user", "moderator"]))):
    """Obtiene la información del usuario actual"""
    from ..auth import get_user_by_id
    user = get_user_by_id(current_user["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return _row_to_user(user)

