from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ..auth import require_role
from ..db import get_conn, put_conn
from ..models import (News, NewsFilters, NewsMetrics, NewsSearchResponse,
                      NewsStats)

router = APIRouter()


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
        # Campos legacy para compatibilidad
        tags=keywords,
        imagenes=imagen_principal,
    )


def build_where_clause(filters: NewsFilters) -> tuple[str, List[Any]]:
    """Construye la cláusula WHERE basada en los filtros"""
    where_conditions = []
    params = []
    
    if filters.q:
        where_conditions.append("(titulo ILIKE %s OR contenido ILIKE %s OR resumen ILIKE %s)")
        like_pattern = f"%{filters.q}%"
        params.extend([like_pattern, like_pattern, like_pattern])
    
    if filters.categoria:
        where_conditions.append("categoria = %s")
        params.append(filters.categoria)
    
    if filters.fuente:
        where_conditions.append("fuente = %s")
        params.append(filters.fuente)
    
    if filters.dominio:
        where_conditions.append("dominio = %s")
        params.append(filters.dominio)
    
    if filters.anio:
        where_conditions.append("anio = %s")
        params.append(filters.anio)
    
    if filters.mes:
        where_conditions.append("mes = %s")
        params.append(filters.mes)
    
    if filters.dia:
        where_conditions.append("dia = %s")
        params.append(filters.dia)
    
    if filters.dia_semana:
        where_conditions.append("dia_semana = %s")
        params.append(filters.dia_semana)
    
    if filters.tipo_contenido:
        where_conditions.append("tipo_contenido = %s")
        params.append(filters.tipo_contenido)
    
    if filters.tiene_imagenes is not None:
        where_conditions.append("tiene_imagenes = %s")
        params.append(filters.tiene_imagenes)
    
    if filters.longitud_titulo_min is not None:
        where_conditions.append("longitud_titulo >= %s")
        params.append(filters.longitud_titulo_min)
    
    if filters.longitud_titulo_max is not None:
        where_conditions.append("longitud_titulo <= %s")
        params.append(filters.longitud_titulo_max)
    
    if filters.longitud_resumen_min is not None:
        where_conditions.append("longitud_resumen >= %s")
        params.append(filters.longitud_resumen_min)
    
    if filters.longitud_resumen_max is not None:
        where_conditions.append("longitud_resumen <= %s")
        params.append(filters.longitud_resumen_max)
    
    if filters.fecha_desde:
        where_conditions.append("fecha >= %s")
        params.append(datetime.strptime(filters.fecha_desde, "%Y-%m-%d"))
    
    if filters.fecha_hasta:
        where_conditions.append("fecha <= %s")
        params.append(datetime.strptime(filters.fecha_hasta, "%Y-%m-%d"))
    
    if filters.keywords:
        where_conditions.append("keywords ILIKE %s")
        params.append(f"%{filters.keywords}%")
    
    where_sql = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    return where_sql, params


@router.get("/search", response_model=NewsSearchResponse)
def advanced_search(
    q: Optional[str] = Query(None, description="Búsqueda de texto en título, contenido o resumen"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    fuente: Optional[str] = Query(None, description="Filtrar por fuente"),
    dominio: Optional[str] = Query(None, description="Filtrar por dominio"),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    mes: Optional[int] = Query(None, description="Filtrar por mes (1-12)"),
    dia: Optional[int] = Query(None, description="Filtrar por día del mes"),
    dia_semana: Optional[str] = Query(None, description="Filtrar por día de la semana"),
    tipo_contenido: Optional[str] = Query(None, description="Filtrar por tipo de contenido"),
    tiene_imagenes: Optional[bool] = Query(None, description="Filtrar por noticias con/sin imágenes"),
    longitud_titulo_min: Optional[int] = Query(None, description="Longitud mínima del título"),
    longitud_titulo_max: Optional[int] = Query(None, description="Longitud máxima del título"),
    longitud_resumen_min: Optional[float] = Query(None, description="Longitud mínima del resumen"),
    longitud_resumen_max: Optional[float] = Query(None, description="Longitud máxima del resumen"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    keywords: Optional[str] = Query(None, description="Búsqueda en keywords"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(20, ge=1, le=100, description="Número de registros a devolver"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Orden de los resultados"),
    include_stats: bool = Query(False, description="Incluir estadísticas en la respuesta"),
    current_user: Optional[dict] = Depends(require_role(["admin", "user", "moderator"], optional=True))
):
    """
    Búsqueda avanzada de noticias con múltiples filtros.
    Requiere autenticación (disponible para todos los usuarios con cuenta).
    """
    # Verificar que el usuario esté autenticado
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Se requiere autenticación para acceder a la búsqueda avanzada. Por favor, inicia sesión."
        )
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Crear objeto de filtros
        filters = NewsFilters(
            q=q, categoria=categoria, fuente=fuente, dominio=dominio,
            anio=anio, mes=mes, dia=dia, dia_semana=dia_semana,
            tipo_contenido=tipo_contenido, tiene_imagenes=tiene_imagenes,
            longitud_titulo_min=longitud_titulo_min, longitud_titulo_max=longitud_titulo_max,
            longitud_resumen_min=longitud_resumen_min, longitud_resumen_max=longitud_resumen_max,
            fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, keywords=keywords
        )
        
        # Construir cláusula WHERE
        where_sql, params = build_where_clause(filters)
        
        # Contar total
        cur.execute(f"SELECT COUNT(*) FROM noticias_limpia {where_sql}", params)
        total = cur.fetchone()[0]
        
        # Obtener datos
        order_sql = "ASC" if order == "asc" else "DESC"
        # Ordenar por fecha (más recientes primero), si fecha es NULL usar fecha_extraccion o created_at como respaldo
        cur.execute(
            f"""
            SELECT id, titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido, 
                   categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
                   cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
                   tipo_contenido, created_at
            FROM noticias_limpia
            {where_sql}
            ORDER BY 
                COALESCE(fecha, fecha_extraccion::date, created_at::date) {order_sql} NULLS LAST,
                fecha_extraccion {order_sql} NULLS LAST,
                created_at {order_sql} NULLS LAST,
                id {order_sql}
            OFFSET %s LIMIT %s
            """,
            params + [skip, limit],
        )
        rows = cur.fetchall()
        items = [_row_to_news(r) for r in rows]
        
        # Obtener estadísticas si se solicitan
        estadisticas = None
        if include_stats:
            estadisticas = get_news_stats(conn, where_sql, params)
        
        return NewsSearchResponse(
            total=total,
            items=items,
            filtros_aplicados=filters,
            estadisticas=estadisticas
        )
    finally:
        put_conn(conn)


@router.get("/stats", response_model=NewsStats)
def get_news_statistics(
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    fuente: Optional[str] = Query(None, description="Filtrar por fuente"),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    current_user: Optional[dict] = Depends(require_role(["admin", "user", "moderator"], optional=True))
):
    """
    Obtiene estadísticas detalladas de las noticias.
    Requiere autenticación (disponible para todos los usuarios con cuenta).
    """
    # Verificar que el usuario esté autenticado
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Se requiere autenticación para acceder a las estadísticas. Por favor, inicia sesión."
        )
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Construir filtros básicos
        where_conditions = []
        params = []
        
        if categoria:
            where_conditions.append("categoria = %s")
            params.append(categoria)
        if fuente:
            where_conditions.append("fuente = %s")
            params.append(fuente)
        if anio:
            where_conditions.append("anio = %s")
            params.append(anio)
        if fecha_desde:
            where_conditions.append("fecha >= %s")
            params.append(datetime.strptime(fecha_desde, "%Y-%m-%d"))
        if fecha_hasta:
            where_conditions.append("fecha <= %s")
            params.append(datetime.strptime(fecha_hasta, "%Y-%m-%d"))
        
        where_sql = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        return get_news_stats(conn, where_sql, params)
    finally:
        put_conn(conn)


def get_news_stats(conn, where_sql: str, params: List[Any]) -> NewsStats:
    """Función auxiliar para obtener estadísticas"""
    cur = conn.cursor()
    
    # Total de noticias
    cur.execute(f"SELECT COUNT(*) FROM noticias_limpia {where_sql}", params)
    total_noticias = cur.fetchone()[0]
    
    # Por fuente
    cur.execute(f"""
        SELECT fuente, COUNT(*) 
        FROM noticias_limpia {where_sql}
        GROUP BY fuente 
        ORDER BY COUNT(*) DESC
    """, params)
    noticias_por_fuente = dict(cur.fetchall())
    
    # Por categoría
    cur.execute(f"""
        SELECT categoria, COUNT(*) 
        FROM noticias_limpia {where_sql}
        WHERE categoria IS NOT NULL AND categoria != ''
        GROUP BY categoria 
        ORDER BY COUNT(*) DESC
    """, params)
    noticias_por_categoria = dict(cur.fetchall())
    
    # Por mes
    cur.execute(f"""
        SELECT mes, COUNT(*) 
        FROM noticias_limpia {where_sql}
        WHERE mes IS NOT NULL
        GROUP BY mes 
        ORDER BY mes
    """, params)
    noticias_por_mes = {str(int(mes)): count for mes, count in cur.fetchall()}
    
    # Por día de la semana
    cur.execute(f"""
        SELECT dia_semana, COUNT(*) 
        FROM noticias_limpia {where_sql}
        WHERE dia_semana IS NOT NULL
        GROUP BY dia_semana 
        ORDER BY COUNT(*) DESC
    """, params)
    noticias_por_dia_semana = dict(cur.fetchall())
    
    # Por tipo de contenido
    cur.execute(f"""
        SELECT tipo_contenido, COUNT(*) 
        FROM noticias_limpia {where_sql}
        WHERE tipo_contenido IS NOT NULL
        GROUP BY tipo_contenido 
        ORDER BY COUNT(*) DESC
    """, params)
    noticias_por_tipo_contenido = dict(cur.fetchall())
    
    # Con/sin imágenes
    cur.execute(f"""
        SELECT 
            SUM(CASE WHEN tiene_imagenes = true THEN 1 ELSE 0 END) as con_imagenes,
            SUM(CASE WHEN tiene_imagenes = false THEN 1 ELSE 0 END) as sin_imagenes
        FROM noticias_limpia {where_sql}
    """, params)
    con_imagenes, sin_imagenes = cur.fetchone()
    
    # Promedios
    cur.execute(f"""
        SELECT 
            AVG(longitud_titulo) as avg_titulo,
            AVG(longitud_resumen) as avg_resumen
        FROM noticias_limpia {where_sql}
        WHERE longitud_titulo IS NOT NULL AND longitud_resumen IS NOT NULL
    """, params)
    avg_titulo, avg_resumen = cur.fetchone()
    
    # Dominios únicos
    cur.execute(f"""
        SELECT COUNT(DISTINCT dominio) 
        FROM noticias_limpia {where_sql}
        WHERE dominio IS NOT NULL
    """, params)
    dominios_unicos = cur.fetchone()[0]
    
    # Rango de fechas
    cur.execute(f"""
        SELECT MIN(fecha), MAX(fecha) 
        FROM noticias_limpia {where_sql}
        WHERE fecha IS NOT NULL
    """, params)
    fecha_min, fecha_max = cur.fetchone()
    
    return NewsStats(
        total_noticias=total_noticias,
        noticias_por_fuente=noticias_por_fuente,
        noticias_por_categoria=noticias_por_categoria,
        noticias_por_mes=noticias_por_mes,
        noticias_por_dia_semana=noticias_por_dia_semana,
        noticias_por_tipo_contenido=noticias_por_tipo_contenido,
        noticias_con_imagenes=con_imagenes or 0,
        noticias_sin_imagenes=sin_imagenes or 0,
        promedio_longitud_titulo=float(avg_titulo) if avg_titulo else 0.0,
        promedio_longitud_resumen=float(avg_resumen) if avg_resumen else 0.0,
        dominios_unicos=dominios_unicos,
        rango_fechas={
            "fecha_min": str(fecha_min) if fecha_min else "",
            "fecha_max": str(fecha_max) if fecha_max else ""
        }
    )


@router.get("/metrics", response_model=NewsMetrics)
def get_news_metrics():
    """Obtiene métricas generales del sistema de noticias"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Métricas básicas
        cur.execute("SELECT COUNT(*) FROM noticias_limpia")
        total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM noticias_limpia WHERE tiene_imagenes = true")
        con_imagenes = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM noticias_limpia WHERE tiene_imagenes = false")
        sin_imagenes = cur.fetchone()[0]
        
        cur.execute("SELECT AVG(longitud_titulo), AVG(longitud_resumen) FROM noticias_limpia")
        avg_titulo, avg_resumen = cur.fetchone()
        
        cur.execute("SELECT COUNT(DISTINCT fuente) FROM noticias_limpia")
        fuentes_activas = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT categoria) FROM noticias_limpia WHERE categoria IS NOT NULL AND categoria != ''")
        categorias_activas = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT dominio) FROM noticias_limpia WHERE dominio IS NOT NULL")
        dominios_unicos = cur.fetchone()[0]
        
        return NewsMetrics(
            total=total,
            con_imagenes=con_imagenes,
            sin_imagenes=sin_imagenes,
            promedio_titulo=float(avg_titulo) if avg_titulo else 0.0,
            promedio_resumen=float(avg_resumen) if avg_resumen else 0.0,
            fuentes_activas=fuentes_activas,
            categorias_activas=categorias_activas,
            dominios_unicos=dominios_unicos
        )
    finally:
        put_conn(conn)


@router.get("/by-year/{year}")
def get_news_by_year(year: int, limit: int = Query(20, ge=1, le=100)):
    """Obtiene noticias de un año específico"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM noticias_limpia WHERE anio = %s", [year])
        total = cur.fetchone()[0]
        
        cur.execute("""
            SELECT id, titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido, 
                   categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
                   cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
                   tipo_contenido, created_at
            FROM noticias_limpia
            WHERE anio = %s
            ORDER BY fecha DESC, id DESC
            LIMIT %s
        """, [year, limit])
        
        rows = cur.fetchall()
        items = [_row_to_news(r) for r in rows]
        
        return {
            "year": year,
            "total": total,
            "items": items
        }
    finally:
        put_conn(conn)


@router.get("/by-month/{year}/{month}")
def get_news_by_month(year: int, month: int, limit: int = Query(20, ge=1, le=100)):
    """Obtiene noticias de un mes específico"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM noticias_limpia WHERE anio = %s AND mes = %s", [year, month])
        total = cur.fetchone()[0]
        
        cur.execute("""
            SELECT id, titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido, 
                   categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
                   cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
                   tipo_contenido, created_at
            FROM noticias_limpia
            WHERE anio = %s AND mes = %s
            ORDER BY fecha DESC, id DESC
            LIMIT %s
        """, [year, month, limit])
        
        rows = cur.fetchall()
        items = [_row_to_news(r) for r in rows]
        
        return {
            "year": year,
            "month": month,
            "total": total,
            "items": items
        }
    finally:
        put_conn(conn)


@router.get("/with-images")
def get_news_with_images(limit: int = Query(20, ge=1, le=100)):
    """Obtiene noticias que tienen imágenes"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM noticias_limpia WHERE tiene_imagenes = true")
        total = cur.fetchone()[0]
        
        cur.execute("""
            SELECT id, titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido, 
                   categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
                   cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
                   tipo_contenido, created_at
            FROM noticias_limpia
            WHERE tiene_imagenes = true
            ORDER BY fecha DESC, id DESC
            LIMIT %s
        """, [limit])
        
        rows = cur.fetchall()
        items = [_row_to_news(r) for r in rows]
        
        return {
            "total": total,
            "items": items
        }
    finally:
        put_conn(conn)


@router.get("/trending")
def get_trending_news(limit: int = Query(10, ge=1, le=50)):
    """Obtiene noticias trending basadas en longitud del título y resumen"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido, 
                   categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
                   cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
                   tipo_contenido, created_at
            FROM noticias_limpia
            WHERE longitud_titulo > 20 AND longitud_resumen > 50
            ORDER BY (longitud_titulo + longitud_resumen) DESC, fecha DESC
            LIMIT %s
        """, [limit])
        
        rows = cur.fetchall()
        items = [_row_to_news(r) for r in rows]
        
        return {
            "total": len(items),
            "items": items
        }
    finally:
        put_conn(conn)
