"""
Router de gestión de API Keys
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth import generate_api_key, require_role
from ..db import get_conn, put_conn
from ..models import (APIKey, APIKeyCreate, APIKeyListResponse, APIKeyStats,
                      APIKeyUpdate)

logger = logging.getLogger(__name__)

router = APIRouter()

# Límites por plan
PLAN_LIMITS = {
    "free": {
        "limite_diario": 50,
        "max_sources": 1,
        "historial_dias": 0,
        "webhooks": 0,
    },
    "pro": {
        "limite_diario": 2000,
        "max_sources": 5,
        "historial_dias": 7,
        "webhooks": 1,
    },
    "business": {
        "limite_diario": 20000,
        "max_sources": 999,  # Ilimitado (usar 999 como máximo)
        "historial_dias": 365,
        "webhooks": 999,  # Ilimitado
    },
    "enterprise": {
        "limite_diario": 999999,  # Ilimitado
        "max_sources": 999,
        "historial_dias": 9999,  # Ilimitado
        "webhooks": 999,
    },
}


def _row_to_api_key(row: tuple) -> APIKey:
    """Convierte una fila de la base de datos a un objeto APIKey"""
    # Orden de campos en la consulta SQL:
    # id, usuario_id, key, nombre, plan, activo, requests_today, requests_total, 
    # last_reset, last_used, fuente_permitida, max_sources, keywords, webhook_url, 
    # historial_dias, limite_diario, created_at, expires_at
    return APIKey(
        id=row[0],
        usuario_id=row[1],
        key=row[2],
        nombre=row[3],
        plan=row[4],
        activo=row[5],
        requests_today=row[6] or 0,
        requests_total=row[7] or 0,
        last_reset=row[8],  # Corregido: era row[9]
        last_used=row[9],   # Corregido: era row[10]
        fuente_permitida=row[10],  # Corregido: era row[11]
        max_sources=row[11] or 1,  # Corregido: era row[12]
        keywords=row[12],   # Corregido: era row[13]
        webhook_url=row[13],  # Corregido: era row[14]
        historial_dias=row[14] or 0,  # Corregido: era row[15]
        limite_diario=row[15] or 50,  # Corregido: era row[16]
        created_at=row[16],  # Corregido: era row[17]
        expires_at=row[17],  # Corregido: era row[18]
    )


@router.get("", response_model=APIKeyListResponse)
def list_api_keys(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    usuario_id: Optional[int] = Query(None),
    activo: Optional[bool] = Query(None),
    plan: Optional[str] = Query(None),
    current_user: dict = Depends(require_role(["admin", "user", "moderator"])),
):
    """Lista API keys"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        where_conditions = []
        params = []
        
        # Los usuarios solo pueden ver sus propias API keys, los admins pueden ver todas
        if current_user["rol"] != "admin":
            where_conditions.append("usuario_id = %s")
            params.append(current_user["id"])
        elif usuario_id is not None:
            where_conditions.append("usuario_id = %s")
            params.append(usuario_id)
        
        if activo is not None:
            where_conditions.append("activo = %s")
            params.append(activo)
        
        if plan:
            where_conditions.append("plan = %s")
            params.append(plan)
        
        where_sql = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Contar total
        cur.execute(f"SELECT COUNT(*) FROM api_keys {where_sql}", params)
        total = cur.fetchone()[0]
        
        # Obtener API keys
        cur.execute(
            f"SELECT id, usuario_id, key, nombre, plan, activo, requests_today, "
            f"requests_total, last_reset, last_used, fuente_permitida, max_sources, "
            f"keywords, webhook_url, historial_dias, limite_diario, created_at, expires_at "
            f"FROM api_keys {where_sql} "
            f"ORDER BY created_at DESC OFFSET %s LIMIT %s",
            params + [skip, limit]
        )
        rows = cur.fetchall()
        
        items = [_row_to_api_key(row) for row in rows]
        
        return APIKeyListResponse(total=total, items=items)
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar API keys: {error_detail}"
        )
    finally:
        put_conn(conn)


@router.get("/{key_id}", response_model=APIKey)
def get_api_key(
    key_id: int,
    current_user: dict = Depends(require_role(["admin", "user", "moderator"])),
):
    """Obtiene una API key por ID"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, usuario_id, key, nombre, plan, activo, requests_today, "
            "requests_total, last_reset, last_used, fuente_permitida, max_sources, "
            "keywords, webhook_url, historial_dias, limite_diario, created_at, expires_at "
            "FROM api_keys WHERE id = %s",
            (key_id,)
        )
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key no encontrada"
            )
        
        # Los usuarios solo pueden ver sus propias API keys
        if current_user["rol"] != "admin" and row[1] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver esta API key"
            )
        
        return _row_to_api_key(row)
    finally:
        put_conn(conn)


@router.post("", response_model=APIKey, status_code=status.HTTP_201_CREATED)
def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(require_role(["admin", "user", "moderator"])),
):
    """Crea una nueva API key"""
    # Los usuarios solo pueden crear API keys para sí mismos, los admins pueden crear para cualquiera
    if current_user["rol"] != "admin" and key_data.usuario_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes crear API keys para otros usuarios"
        )
    
    # Verificar que el usuario existe
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, plan FROM usuarios WHERE id = %s", (key_data.usuario_id,))
        user = cur.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Obtener límites del plan
        user_plan = key_data.plan or user[1]  # Usar el plan del usuario si no se especifica
        limits = PLAN_LIMITS.get(user_plan, PLAN_LIMITS["free"])
        
        # Aplicar límites según el plan
        limite_diario = key_data.limite_diario or limits["limite_diario"]
        max_sources = key_data.max_sources or limits["max_sources"]
        historial_dias = key_data.historial_dias if key_data.historial_dias is not None else limits["historial_dias"]
        
        # Validar límites según plan
        if limite_diario > limits["limite_diario"]:
            limite_diario = limits["limite_diario"]
        if max_sources > limits["max_sources"]:
            max_sources = limits["max_sources"]
        
        # Generar API key
        api_key = generate_api_key()
        
        # Insertar API key
        cur.execute(
            "INSERT INTO api_keys (usuario_id, key, nombre, plan, limite_diario, "
            "fuente_permitida, max_sources, keywords, webhook_url, historial_dias, expires_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "RETURNING id, usuario_id, key, nombre, plan, activo, requests_today, "
            "requests_total, last_reset, last_used, fuente_permitida, max_sources, "
            "keywords, webhook_url, historial_dias, limite_diario, created_at, expires_at",
            (
                key_data.usuario_id,
                api_key,
                key_data.nombre,
                user_plan,
                limite_diario,
                key_data.fuente_permitida,
                max_sources,
                key_data.keywords,
                key_data.webhook_url,
                historial_dias,
                key_data.expires_at,
            )
        )
        row = cur.fetchone()
        conn.commit()
        
        return _row_to_api_key(row)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear API key: {str(e)}"
        )
    finally:
        put_conn(conn)


@router.put("/{key_id}", response_model=APIKey)
def update_api_key(
    key_id: int,
    key_data: APIKeyUpdate,
    current_user: dict = Depends(require_role(["admin", "user", "moderator"])),
):
    """Actualiza una API key"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Obtener API key actual
        cur.execute(
            "SELECT id, usuario_id, plan FROM api_keys WHERE id = %s",
            (key_id,)
        )
        existing = cur.fetchone()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key no encontrada"
            )
        
        # Los usuarios solo pueden actualizar sus propias API keys
        if current_user["rol"] != "admin" and existing[1] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para actualizar esta API key"
            )
        
        # Obtener límites del plan actual
        plan = key_data.plan or existing[2]
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
        
        # Construir query de actualización
        updates = []
        params = []
        
        if key_data.nombre is not None:
            updates.append("nombre = %s")
            params.append(key_data.nombre)
        
        if key_data.plan is not None:
            updates.append("plan = %s")
            params.append(key_data.plan)
            # Actualizar límites según nuevo plan
            limits = PLAN_LIMITS.get(key_data.plan, PLAN_LIMITS["free"])
        
        if key_data.activo is not None:
            updates.append("activo = %s")
            params.append(key_data.activo)
        
        if key_data.limite_diario is not None:
            limite = min(key_data.limite_diario, limits["limite_diario"])
            updates.append("limite_diario = %s")
            params.append(limite)
        
        if key_data.fuente_permitida is not None:
            updates.append("fuente_permitida = %s")
            params.append(key_data.fuente_permitida)
        
        if key_data.max_sources is not None:
            max_src = min(key_data.max_sources, limits["max_sources"])
            updates.append("max_sources = %s")
            params.append(max_src)
        
        if key_data.keywords is not None:
            updates.append("keywords = %s")
            params.append(key_data.keywords)
        
        if key_data.webhook_url is not None:
            updates.append("webhook_url = %s")
            params.append(key_data.webhook_url)
        
        if key_data.historial_dias is not None:
            hist = min(key_data.historial_dias, limits["historial_dias"])
            updates.append("historial_dias = %s")
            params.append(hist)
        
        if key_data.expires_at is not None:
            updates.append("expires_at = %s")
            params.append(key_data.expires_at)
        
        if not updates:
            # Si no hay cambios, obtener y retornar la API key actual
            cur.execute(
                "SELECT id, usuario_id, key, nombre, plan, activo, requests_today, "
                "requests_total, last_reset, last_used, fuente_permitida, max_sources, "
                "keywords, webhook_url, historial_dias, limite_diario, created_at, expires_at "
                "FROM api_keys WHERE id = %s",
                (key_id,)
            )
            return _row_to_api_key(cur.fetchone())
        
        params.append(key_id)
        cur.execute(
            f"UPDATE api_keys SET {', '.join(updates)} WHERE id = %s "
            "RETURNING id, usuario_id, key, nombre, plan, activo, requests_today, "
            "requests_total, last_reset, last_used, fuente_permitida, max_sources, "
            "keywords, webhook_url, historial_dias, limite_diario, created_at, expires_at",
            params
        )
        row = cur.fetchone()
        
        # Si se actualizó el plan, sincronizar con el usuario asociado
        if key_data.plan is not None:
            usuario_id = existing[1]  # existing[1] es usuario_id
            cur.execute(
                "UPDATE usuarios SET plan = %s WHERE id = %s",
                (key_data.plan, usuario_id)
            )
            # También actualizar todas las demás API keys del mismo usuario para mantener consistencia
            cur.execute(
                "UPDATE api_keys SET plan = %s WHERE usuario_id = %s AND id != %s",
                (key_data.plan, usuario_id, key_id)
            )
            logger.info(f"✅ Plan sincronizado: API Key {key_id} -> Plan {key_data.plan} -> Usuario {usuario_id} y todas sus API keys actualizadas")
        
        conn.commit()
        
        return _row_to_api_key(row)
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar API key: {str(e)}"
        )
    finally:
        put_conn(conn)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(
    key_id: int,
    current_user: dict = Depends(require_role(["admin", "user", "moderator"])),
):
    """Elimina una API key"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Verificar que la API key existe y obtener el usuario_id
        cur.execute("SELECT usuario_id FROM api_keys WHERE id = %s", (key_id,))
        result = cur.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key no encontrada"
            )
        
        # Los usuarios solo pueden eliminar sus propias API keys
        if current_user["rol"] != "admin" and result[0] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para eliminar esta API key"
            )
        
        cur.execute("DELETE FROM api_keys WHERE id = %s", (key_id,))
        conn.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar API key: {str(e)}"
        )
    finally:
        put_conn(conn)


@router.get("/{key_id}/stats", response_model=APIKeyStats)
def get_api_key_stats(
    key_id: int,
    current_user: dict = Depends(require_role(["admin", "user", "moderator"])),
):
    """Obtiene estadísticas de uso de una API key"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT requests_today, requests_total, limite_diario, last_used "
            "FROM api_keys WHERE id = %s",
            (key_id,)
        )
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key no encontrada"
            )
        
        requests_today, requests_total, limite_diario, last_used = row
        
        porcentaje_uso = (requests_today / limite_diario * 100) if limite_diario > 0 else 0
        
        return APIKeyStats(
            requests_today=requests_today,
            requests_total=requests_total,
            limite_diario=limite_diario,
            porcentaje_uso=round(porcentaje_uso, 2),
            last_used=last_used,
        )
    finally:
        put_conn(conn)

