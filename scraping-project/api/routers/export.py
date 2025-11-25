"""
Router de exportación de noticias
Permite exportar noticias en diferentes formatos: JSON, CSV, XML, Parquet
Con restricciones según el plan del usuario
"""
import csv
import io
import json
from datetime import datetime
from typing import Any, List, Optional, Union

# Importaciones opcionales para formatos avanzados
try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False
    pa = None
    pq = None

try:
    from lxml import etree
    XML_AVAILABLE = True
except ImportError:
    XML_AVAILABLE = False
    etree = None

from fastapi import (APIRouter, Depends, HTTPException, Query, Response,
                     Security)
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials

from ..auth import (get_current_api_key, get_current_user, require_role,
                    security)
from ..db import get_conn, put_conn
from ..models import News

router = APIRouter()

# Límites de exportación por plan
EXPORT_LIMITS = {
    "free": {
        "formats": ["json"],  # Solo JSON
        "max_records": 50,
        "allowed": True,
    },
    "pro": {
        "formats": ["json", "csv"],  # JSON y CSV
        "max_records": 2000,
        "allowed": True,
    },
    "business": {
        "formats": ["json", "csv", "xml"],  # JSON, CSV, XML
        "max_records": 20000,
        "allowed": True,
    },
    "enterprise": {
        "formats": ["json", "csv", "xml", "parquet"],  # Todos los formatos
        "max_records": 999999,  # Ilimitado
        "allowed": True,
    },
}


def _row_to_news(row: tuple) -> News:
    """Convierte una fila de la base de datos a un objeto News"""
    (
        id,
        titulo,
        fecha,
        hora,
        anio,
        mes,
        dia,
        dia_semana,
        resumen,
        contenido,
        categoria,
        autor,
        keywords,
        url,
        dominio,
        fecha_extraccion,
        imagen_principal,
        cantidad_imagenes,
        tiene_imagenes,
        fuente,
        longitud_titulo,
        longitud_resumen,
        tipo_contenido,
        created_at,
    ) = row
    return News(
        id=id,
        titulo=titulo,
        fecha=fecha,
        hora=hora,
        anio=anio,
        mes=mes,
        dia=dia,
        dia_semana=dia_semana,
        resumen=resumen,
        contenido=contenido,
        categoria=categoria,
        autor=autor,
        keywords=keywords,
        url=url,
        dominio=dominio,
        fecha_extraccion=fecha_extraccion,
        imagen_principal=imagen_principal,
        cantidad_imagenes=cantidad_imagenes,
        tiene_imagenes=tiene_imagenes,
        fuente=fuente,
        longitud_titulo=longitud_titulo,
        longitud_resumen=longitud_resumen,
        tipo_contenido=tipo_contenido,
        created_at=created_at,
        tags=keywords,
        imagenes=imagen_principal,
    )


def _news_to_dict(news: News) -> dict:
    """Convierte un objeto News a diccionario"""
    return {
        "id": news.id,
        "titulo": news.titulo,
        "fecha": news.fecha.isoformat() if news.fecha else None,
        "hora": str(news.hora) if news.hora else None,
        "anio": news.anio,
        "mes": news.mes,
        "dia": news.dia,
        "dia_semana": news.dia_semana,
        "resumen": news.resumen,
        "contenido": news.contenido,
        "categoria": news.categoria,
        "autor": news.autor,
        "keywords": news.keywords,
        "url": news.url,
        "dominio": news.dominio,
        "fecha_extraccion": news.fecha_extraccion.isoformat() if news.fecha_extraccion else None,
        "imagen_principal": news.imagen_principal,
        "cantidad_imagenes": news.cantidad_imagenes,
        "tiene_imagenes": news.tiene_imagenes,
        "fuente": news.fuente,
        "longitud_titulo": news.longitud_titulo,
        "longitud_resumen": news.longitud_resumen,
        "tipo_contenido": news.tipo_contenido,
        "created_at": news.created_at.isoformat() if news.created_at else None,
    }


def _build_social_where_export(where: List[str], params: List[Any]) -> tuple[str, List[Any]]:
    """Construye WHERE clause y parámetros para social_news en exportación"""
    social_where = []
    social_params = []
    param_idx = 0
    
    for condition in where:
        if "titulo ILIKE" in condition:
            social_where.append("titulo ILIKE %s")
            social_params.append(params[param_idx])
            param_idx += 1
        elif "contenido ILIKE" in condition:
            param_idx += 1  # No aplica a social_news
        elif "resumen ILIKE" in condition:
            social_where.append("resumen ILIKE %s")
            social_params.append(params[param_idx])
            param_idx += 1
        elif "categoria = %s" in condition:
            social_where.append("categoria = %s")
            social_params.append(params[param_idx])
            param_idx += 1
        elif "fuente = %s" in condition:
            social_where.append("fuente = %s")
            social_params.append(params[param_idx])
            param_idx += 1
        elif "fecha >=" in condition:
            social_where.append("fecha >= %s")
            social_params.append(params[param_idx])
            param_idx += 1
        elif "fecha <=" in condition:
            social_where.append("fecha <= %s")
            social_params.append(params[param_idx])
            param_idx += 1
        else:
            if "%s" in condition:
                param_idx += condition.count("%s")
    
    social_where_sql = f"WHERE {' AND '.join(social_where)}" if social_where else ""
    return social_where_sql, social_params


def _get_news_query(
    q: Optional[str] = None,
    categoria: Optional[str] = None,
    fuente: Optional[str] = None,
    dominio: Optional[str] = None,
    anio: Optional[int] = None,
    mes: Optional[int] = None,
    dia_semana: Optional[str] = None,
    tipo_contenido: Optional[str] = None,
    tiene_imagenes: Optional[bool] = None,
    keywords: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: Optional[int] = None,
    order: str = "desc",
) -> tuple[str, List[Any]]:
    """Construye la consulta SQL y parámetros para obtener noticias de ambas tablas"""
    where = []
    params: List[Any] = []

    if q:
        where.append("(titulo ILIKE %s OR contenido ILIKE %s OR resumen ILIKE %s)")
        like = f"%{q}%"
        params.extend([like, like, like])
    if categoria:
        where.append("categoria = %s")
        params.append(categoria)
    if fuente:
        where.append("fuente = %s")
        params.append(fuente)
    if dominio:
        where.append("dominio = %s")
        params.append(dominio)
    if anio:
        where.append("anio = %s")
        params.append(anio)
    if mes:
        where.append("mes = %s")
        params.append(mes)
    if dia_semana:
        where.append("dia_semana = %s")
        params.append(dia_semana)
    if tipo_contenido:
        where.append("tipo_contenido = %s")
        params.append(tipo_contenido)
    if tiene_imagenes is not None:
        where.append("tiene_imagenes = %s")
        params.append(tiene_imagenes)
    if keywords:
        where.append("keywords ILIKE %s")
        params.append(f"%{keywords}%")
    if date_from:
        where.append("fecha >= %s")
        params.append(date_from)
    if date_to:
        where.append("fecha <= %s")
        params.append(date_to)

    where_clause = " AND ".join(where) if where else "1=1"
    order_clause = "DESC" if order == "desc" else "ASC"
    
    # Construir WHERE para social_news
    social_where_sql, social_params = _build_social_where_export(where, params)
    
    limit_clause = ""
    if limit:
        limit_clause = f"LIMIT {limit}"

    # Query para noticias_limpia
    query1 = f"""
        SELECT id, titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido,
               categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
               cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
               tipo_contenido, created_at
        FROM noticias_limpia
        WHERE {where_clause}
    """
    
    # Query para social_news
    query2 = f"""
        SELECT 
            id + 1000000 as id,
            titulo,
            fecha::timestamp as fecha,
            NULL::time as hora,
            EXTRACT(YEAR FROM fecha)::float as anio,
            EXTRACT(MONTH FROM fecha)::float as mes,
            EXTRACT(DAY FROM fecha)::float as dia,
            TO_CHAR(fecha, 'Day') as dia_semana,
            resumen,
            resumen as contenido,
            categoria,
            NULL as autor,
            NULL as keywords,
            url,
            NULL as dominio,
            created_at as fecha_extraccion,
            imagen as imagen_principal,
            CASE WHEN imagen IS NOT NULL THEN 1 ELSE 0 END as cantidad_imagenes,
            CASE WHEN imagen IS NOT NULL THEN true ELSE false END as tiene_imagenes,
            fuente,
            LENGTH(titulo) as longitud_titulo,
            LENGTH(resumen)::float as longitud_resumen,
            'social' as tipo_contenido,
            created_at
        FROM social_news
        {social_where_sql}
    """
    
    # UNION ALL para combinar ambas tablas
    query = f"""
        SELECT * FROM (
            {query1}
            UNION ALL
            {query2}
        ) AS combined_news
        ORDER BY fecha_extraccion {order_clause}
        {limit_clause}
    """
    
    # Combinar parámetros
    final_params = params.copy() + social_params
    if limit:
        # El limit ya no se pasa como parámetro, está en la query
        pass
    
    return query, final_params


def _export_json(news_list: List[News]) -> bytes:
    """Exporta noticias a formato JSON"""
    data = [_news_to_dict(news) for news in news_list]
    return json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')


def _export_csv(news_list: List[News]) -> bytes:
    """Exporta noticias a formato CSV"""
    if not news_list:
        return b""
    
    output = io.StringIO()
    fieldnames = [
        "id", "titulo", "fecha", "hora", "anio", "mes", "dia", "dia_semana",
        "resumen", "contenido", "categoria", "autor", "keywords", "url", "dominio",
        "fecha_extraccion", "imagen_principal", "cantidad_imagenes", "tiene_imagenes",
        "fuente", "longitud_titulo", "longitud_resumen", "tipo_contenido", "created_at"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    
    for news in news_list:
        row = _news_to_dict(news)
        writer.writerow(row)
    
    return output.getvalue().encode('utf-8')


def _export_xml(news_list: List[News]) -> bytes:
    """Exporta noticias a formato XML"""
    if not XML_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="El formato XML no está disponible. Por favor, instala lxml: pip install lxml"
        )
    
    root = etree.Element("noticias")
    root.set("total", str(len(news_list)))
    root.set("fecha_exportacion", datetime.now().isoformat())
    
    for news in news_list:
        noticia_elem = etree.SubElement(root, "noticia")
        news_dict = _news_to_dict(news)
        
        for key, value in news_dict.items():
            if value is not None:
                elem = etree.SubElement(noticia_elem, key)
                elem.text = str(value)
    
    return etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True)


def _export_parquet(news_list: List[News]) -> bytes:
    """Exporta noticias a formato Parquet"""
    if not PARQUET_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="El formato Parquet no está disponible. Por favor, instala pyarrow: pip install pyarrow"
        )
    
    if not news_list:
        return b""
    
    # Convertir a lista de diccionarios
    data = [_news_to_dict(news) for news in news_list]
    
    # Convertir a tabla PyArrow
    table = pa.Table.from_pylist(data)
    
    # Escribir a buffer en memoria
    buffer = io.BytesIO()
    pq.write_table(table, buffer)
    buffer.seek(0)
    
    return buffer.read()


async def get_auth_info(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    """Obtiene información de autenticación (usuario o API key)"""
    from fastapi import status

    from ..auth import get_api_key, get_user_by_id, verify_token
    
    token = credentials.credentials
    
    # Intentar primero como API key (las API keys empiezan con "biz_")
    if token.startswith("biz_"):
        try:
            key_data = get_api_key(token)
            if key_data:
                return {
                    "type": "api_key",
                    "plan": key_data[4],
                    "data": {
                        "id": key_data[0],
                        "usuario_id": key_data[1],
                        "plan": key_data[4],
                    }
                }
        except Exception as e:
            pass
    
    # Si no es API key, intentar como JWT
    try:
        payload = verify_token(token)
        if payload:
            user = get_user_by_id(payload.get("sub"))
            if user:
                return {
                    "type": "user",
                    "plan": user[7],
                    "data": {
                        "id": user[0],
                        "email": user[1],
                        "plan": user[7],
                    }
                }
    except Exception as e:
        pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token o API key inválidos",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/export")
async def export_news(
    format: str = Query(..., description="Formato de exportación: json, csv, xml, parquet"),
    q: Optional[str] = Query(None, description="Texto a buscar"),
    categoria: Optional[str] = Query(None),
    fuente: Optional[str] = Query(None),
    dominio: Optional[str] = Query(None),
    anio: Optional[int] = Query(None),
    mes: Optional[int] = Query(None),
    dia_semana: Optional[str] = Query(None),
    tipo_contenido: Optional[str] = Query(None),
    tiene_imagenes: Optional[bool] = Query(None),
    keywords: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1),
    order: str = Query("desc", regex="^(asc|desc)$"),
    auth_info: dict = Depends(get_auth_info),
):
    """
    Exporta noticias en diferentes formatos según el plan del usuario o API key.
    
    Puede autenticarse con:
    - Token JWT (Bearer token) - obtiene el plan del usuario
    - API Key (Bearer token con API key) - obtiene el plan de la API key
    
    Formatos disponibles por plan:
    - FREE: JSON (máx 50 registros)
    - PRO: JSON, CSV (máx 2000 registros)
    - BUSINESS: JSON, CSV, XML (máx 20000 registros)
    - ENTERPRISE: JSON, CSV, XML, Parquet (ilimitado)
    """
    # Obtener plan del usuario o API key
    user_plan = auth_info.get("plan", "free")
    plan_limits = EXPORT_LIMITS.get(user_plan, EXPORT_LIMITS["free"])
    
    # Verificar que el formato esté permitido
    format_lower = format.lower()
    if format_lower not in plan_limits["formats"]:
        raise HTTPException(
            status_code=403,
            detail=f"El formato '{format}' no está disponible en tu plan ({user_plan.upper()}). "
                   f"Formatos disponibles: {', '.join(plan_limits['formats'])}"
        )
    
    # Verificar límite de registros
    max_records = plan_limits["max_records"]
    if limit and limit > max_records:
        limit = max_records
    elif not limit:
        limit = max_records
    
    # Obtener noticias
    conn = get_conn()
    try:
        cur = conn.cursor()
        query, params = _get_news_query(
            q=q,
            categoria=categoria,
            fuente=fuente,
            dominio=dominio,
            anio=anio,
            mes=mes,
            dia_semana=dia_semana,
            tipo_contenido=tipo_contenido,
            tiene_imagenes=tiene_imagenes,
            keywords=keywords,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            order=order,
        )
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        # Convertir a objetos News
        news_list = [_row_to_news(row) for row in rows]
        
        # Exportar según el formato
        if format_lower == "json":
            content = _export_json(news_list)
            media_type = "application/json"
            filename = f"noticias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        elif format_lower == "csv":
            content = _export_csv(news_list)
            media_type = "text/csv"
            filename = f"noticias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        elif format_lower == "xml":
            content = _export_xml(news_list)
            media_type = "application/xml"
            filename = f"noticias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        elif format_lower == "parquet":
            content = _export_parquet(news_list)
            media_type = "application/octet-stream"
            filename = f"noticias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
        else:
            raise HTTPException(status_code=400, detail=f"Formato no soportado: {format}")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Total-Records": str(len(news_list)),
                "X-Plan": user_plan,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al exportar noticias: {str(e)}")
    finally:
        put_conn(conn)


@router.get("/export/info")
async def get_export_info(
    auth_info: dict = Depends(get_auth_info),
):
    """Obtiene información sobre las capacidades de exportación del plan actual"""
    user_plan = auth_info.get("plan", "free")
    plan_limits = EXPORT_LIMITS.get(user_plan, EXPORT_LIMITS["free"])
    
    return {
        "plan": user_plan,
        "formats_available": plan_limits["formats"],
        "max_records": plan_limits["max_records"],
        "allowed": plan_limits["allowed"],
    }

