"""
Módulo de autenticación y seguridad
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError

from .db import get_conn, put_conn

# Configuración JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas
REFRESH_TOKEN_EXPIRE_DAYS = 30

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def generate_api_key() -> str:
    """Genera una API key segura"""
    return f"biz_{secrets.token_urlsafe(32)}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Crea un refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verifica y decodifica un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError:
        return None


def get_user_by_email(email: str) -> Optional[tuple]:
    """Obtiene un usuario por email"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, password_hash, nombre, apellido, activo, rol, plan, "
            "created_at, updated_at, last_login, email_verificado "
            "FROM usuarios WHERE email = %s",
            (email,)
        )
        return cur.fetchone()
    finally:
        put_conn(conn)


def get_user_by_id(user_id: int) -> Optional[tuple]:
    """Obtiene un usuario por ID"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, email, password_hash, nombre, apellido, activo, rol, plan, "
            "created_at, updated_at, last_login, email_verificado "
            "FROM usuarios WHERE id = %s",
            (user_id,)
        )
        return cur.fetchone()
    finally:
        put_conn(conn)


def update_last_login(user_id: int):
    """Actualiza el último login del usuario"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE usuarios SET last_login = %s WHERE id = %s",
            (datetime.utcnow(), user_id)
        )
        conn.commit()
    finally:
        put_conn(conn)


def get_api_key(key: str) -> Optional[tuple]:
    """Obtiene una API key de la base de datos"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, usuario_id, key, nombre, plan, activo, requests_today, "
            "requests_total, last_reset, last_used, fuente_permitida, max_sources, "
            "keywords, webhook_url, historial_dias, limite_diario, created_at, expires_at "
            "FROM api_keys WHERE key = %s AND activo = true",
            (key,)
        )
        return cur.fetchone()
    finally:
        put_conn(conn)


def increment_api_key_usage(api_key_id: int):
    """Incrementa el contador de uso de una API key"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        # Verificar si necesitamos resetear el contador diario
        cur.execute(
            "SELECT last_reset FROM api_keys WHERE id = %s",
            (api_key_id,)
        )
        result = cur.fetchone()
        if result:
            last_reset = result[0]
            today = datetime.utcnow().date()
            if last_reset != today:
                # Resetear contador diario
                cur.execute(
                    "UPDATE api_keys SET requests_today = 1, last_reset = %s, requests_total = requests_total + 1 WHERE id = %s",
                    (today, api_key_id)
                )
            else:
                # Incrementar contadores
                cur.execute(
                    "UPDATE api_keys SET requests_today = requests_today + 1, requests_total = requests_total + 1, last_used = %s WHERE id = %s",
                    (datetime.utcnow(), api_key_id)
                )
        conn.commit()
    finally:
        put_conn(conn)


def check_api_key_limit(api_key_data: tuple) -> bool:
    """Verifica si una API key ha excedido su límite diario"""
    limite_diario = api_key_data[16]  # índice del campo limite_diario
    requests_today = api_key_data[6]  # índice del campo requests_today
    last_reset = api_key_data[9]  # índice del campo last_reset
    
    # Verificar si el contador necesita resetearse
    today = datetime.utcnow().date()
    if last_reset != today:
        return True  # Se puede resetear, así que está disponible
    
    return requests_today < limite_diario


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Obtiene el usuario actual desde el token JWT"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_id(user_id)
    if user is None or not user[5]:  # user[5] es el campo 'activo'
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "id": user[0],
        "email": user[1],
        "nombre": user[3],
        "apellido": user[4],
        "rol": user[6],
        "plan": user[7],
    }


async def get_current_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Obtiene y valida una API key desde el header"""
    api_key = credentials.credentials
    
    key_data = get_api_key(api_key)
    
    if key_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida o inactiva",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar expiración
    expires_at = key_data[17]
    if expires_at and expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key expirada",
        )
    
    # Verificar límite diario
    if not check_api_key_limit(key_data):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Límite diario de requests excedido",
        )
    
    # Incrementar contador
    increment_api_key_usage(key_data[0])
    
    return {
        "id": key_data[0],
        "usuario_id": key_data[1],
        "key": key_data[2],
        "plan": key_data[4],
        "limite_diario": key_data[16],
        "fuente_permitida": key_data[10],
        "max_sources": key_data[11],
    }


def require_role(allowed_roles: list[str], optional: bool = False):
    """Decorador para requerir roles específicos"""
    if optional:
        def role_checker_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[dict]:
            if not credentials:
                return None
            try:
                token = credentials.credentials
                payload = verify_token(token)
                if payload is None:
                    return None
                user_id: int = payload.get("sub")
                if user_id is None:
                    return None
                user = get_user_by_id(user_id)
                if user is None or not user[5]:  # user[5] es el campo 'activo'
                    return None
                current_user = {
                    "id": user[0],
                    "email": user[1],
                    "nombre": user[3],
                    "apellido": user[4],
                    "rol": user[6],
                    "plan": user[7],
                }
                if current_user["rol"] not in allowed_roles:
                    return None
                return current_user
            except:
                return None
        return role_checker_optional
    else:
        def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
            if current_user["rol"] not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos suficientes"
                )
            return current_user
        return role_checker


def require_plan(allowed_plans: list[str]):
    """Decorador para requerir planes específicos"""
    def plan_checker(api_key: dict = Depends(get_current_api_key)) -> dict:
        if api_key["plan"] not in allowed_plans:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Esta funcionalidad requiere uno de estos planes: {', '.join(allowed_plans)}"
            )
        return api_key
    return plan_checker

