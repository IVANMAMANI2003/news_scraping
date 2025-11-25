from datetime import date, datetime, time
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..db import get_conn, put_conn
from ..models import News, NewsListResponse

router = APIRouter()


def _row_to_news(row: tuple) -> News:
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
        tags=keywords,  # Mapear keywords a tags
        imagenes=imagen_principal,  # Mapear imagen_principal a imagenes
    )


def _build_social_where(where: list[str], params: list[Any]) -> tuple[str, list[Any]]:
    """Construye WHERE clause y parámetros para social_news (solo filtros aplicables)"""
    social_where = []
    social_params = []
    param_idx = 0
    
    for condition in where:
        if "titulo ILIKE" in condition:
            social_where.append("titulo ILIKE %s")
            social_params.append(params[param_idx])
            param_idx += 1
        elif "contenido ILIKE" in condition:
            # No aplica a social_news, pero avanzamos el índice
            param_idx += 1
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
            # Otros filtros no aplican a social_news, pero avanzamos el índice
            if "%s" in condition:
                param_idx += condition.count("%s")
    
    social_where_sql = f"WHERE {' AND '.join(social_where)}" if social_where else ""
    return social_where_sql, social_params


@router.get("", response_model=NewsListResponse)
def list_news(
    q: Optional[str] = Query(None, description="Texto a buscar en título, contenido o resumen"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    fuente: Optional[str] = Query(None, description="Filtrar por fuente"),
    dominio: Optional[str] = Query(None, description="Filtrar por dominio"),
    anio: Optional[int] = Query(None, description="Filtrar por año"),
    mes: Optional[int] = Query(None, description="Filtrar por mes (1-12)"),
    dia_semana: Optional[str] = Query(None, description="Filtrar por día de la semana"),
    tipo_contenido: Optional[str] = Query(None, description="Filtrar por tipo de contenido"),
    tiene_imagenes: Optional[bool] = Query(None, description="Filtrar por noticias con/sin imágenes"),
    keywords: Optional[str] = Query(None, description="Búsqueda en keywords"),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1),
    order: str = Query("desc", regex="^(asc|desc)$"),
):
    conn = get_conn()
    try:
        cur = conn.cursor()
        where = []
        params: list[Any] = []

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
            params.append(datetime.strptime(date_from, "%Y-%m-%d"))
        if date_to:
            where.append("fecha <= %s")
            params.append(datetime.strptime(date_to, "%Y-%m-%d"))

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        # Count total de ambas tablas
        count_query1 = f"SELECT COUNT(*) FROM noticias_limpia {where_sql}"
        cur.execute(count_query1, params)
        count1 = cur.fetchone()[0]
        
        # Count de social_news (solo filtros aplicables) - COMENTADO TEMPORALMENTE
        # social_where_sql, social_params = _build_social_where(where, params)
        # count_query2 = f"SELECT COUNT(*) FROM social_news {social_where_sql}"
        # cur.execute(count_query2, social_params)
        # count2 = cur.fetchone()[0]
        
        # total = count1 + count2
        total = count1  # Solo contar noticias_limpia

        # Data usando UNION ALL
        order_sql = "ASC" if order == "asc" else "DESC"
        effective_limit = limit if limit is not None else max(total - skip, 0)
        
        # Query para noticias_limpia
        query1 = f"""
            SELECT id, titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido, 
                   categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
                   cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
                   tipo_contenido, created_at
            FROM noticias_limpia
            {where_sql}
        """
        
        # Query para social_news (mapear campos faltantes) - COMENTADO TEMPORALMENTE
        # query2 = f"""
        #     SELECT 
        #         id + 1000000 as id,  -- Offset para evitar conflictos de IDs
        #         titulo,
        #         fecha::timestamp as fecha,
        #         NULL::time as hora,
        #         EXTRACT(YEAR FROM fecha)::float as anio,
        #         EXTRACT(MONTH FROM fecha)::float as mes,
        #         EXTRACT(DAY FROM fecha)::float as dia,
        #         TO_CHAR(fecha, 'Day') as dia_semana,
        #         resumen,
        #         resumen as contenido,  -- Usar resumen como contenido
        #         categoria,
        #         NULL as autor,
        #         NULL as keywords,
        #         url,
        #         NULL as dominio,
        #         created_at as fecha_extraccion,
        #         imagen as imagen_principal,
        #         CASE WHEN imagen IS NOT NULL THEN 1 ELSE 0 END as cantidad_imagenes,
        #         CASE WHEN imagen IS NOT NULL THEN true ELSE false END as tiene_imagenes,
        #         fuente,
        #         LENGTH(titulo) as longitud_titulo,
        #         LENGTH(resumen)::float as longitud_resumen,
        #         'social' as tipo_contenido,
        #         created_at
        #     FROM social_news
        #     {social_where_sql}
        # """
        
        # UNION ALL para combinar ambas tablas - COMENTADO TEMPORALMENTE
        # union_query = f"""
        #     SELECT * FROM (
        #         {query1}
        #         UNION ALL
        #         {query2}
        #     ) AS combined_news
        #     ORDER BY fecha {order_sql} NULLS LAST, id {order_sql}
        #     OFFSET %s LIMIT %s
        # """
        
        # Solo usar query1 (noticias_limpia) - COMENTADO social_news
        # Ordenar por fecha (más recientes primero), si fecha es NULL usar fecha_extraccion o created_at como respaldo
        union_query = f"""
            {query1}
            ORDER BY 
                COALESCE(fecha, fecha_extraccion::date, created_at::date) {order_sql} NULLS LAST,
                fecha_extraccion {order_sql} NULLS LAST,
                created_at {order_sql} NULLS LAST,
                id {order_sql}
            OFFSET %s LIMIT %s
        """
        
        # Combinar parámetros: solo los de noticias_limpia, luego skip y limit
        # final_params = params.copy() + social_params + [skip, effective_limit]
        final_params = params.copy() + [skip, effective_limit]
        
        cur.execute(union_query, final_params)
        rows = cur.fetchall()
        items = [_row_to_news(r) for r in rows]
        return NewsListResponse(total=total, items=items)
    finally:
        put_conn(conn)


@router.get("/{news_id}", response_model=News)
def get_news(news_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido, 
                   categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
                   cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
                   tipo_contenido, created_at
            FROM noticias_limpia WHERE id = %s
            """,
            [news_id],
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Noticia no encontrada")
        return _row_to_news(row)
    finally:
        put_conn(conn)


@router.get("/categorias/listar", response_model=List[str])
def list_categorias():
    """Obtiene la lista de todas las categorías disponibles"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT categoria FROM noticias_limpia 
            WHERE categoria IS NOT NULL AND categoria != ''
            ORDER BY categoria
            """
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]
    finally:
        put_conn(conn)


@router.get("/fuentes/listar", response_model=List[str])
def list_fuentes():
    """Obtiene la lista de todas las fuentes disponibles de noticias_limpia y social_news"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT fuente 
            FROM (
                SELECT fuente FROM noticias_limpia 
                WHERE fuente IS NOT NULL AND fuente != ''
                UNION
                SELECT fuente FROM social_news
                WHERE fuente IS NOT NULL AND fuente != ''
            ) AS combined_fuentes
            ORDER BY fuente
            """
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]
    finally:
        put_conn(conn)


@router.get("/fuentes/{fuente_name}", response_model=NewsListResponse)
def get_news_by_fuente(
    fuente_name: str,
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1),
    order: str = Query("desc", regex="^(asc|desc)$"),
    fecha_desde: str = Query(None, description="Fecha desde (YYYY-MM-DD)"),
):
    """Obtiene todas las noticias de una fuente específica de ambas tablas"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Construir query con filtro de fecha
        where_clause = "fuente = %s"
        params = [fuente_name]
        
        if fecha_desde:
            where_clause += " AND fecha >= %s"
            params.append(fecha_desde)
        
        # Count de ambas tablas
        cur.execute(
            f"SELECT COUNT(*) FROM noticias_limpia WHERE {where_clause}",
            params
        )
        count1 = cur.fetchone()[0]
        
        cur.execute(
            f"SELECT COUNT(*) FROM social_news WHERE {where_clause}",
            params
        )
        count2 = cur.fetchone()[0]
        
        total = count1 + count2
        
        # Data usando UNION
        order_sql = "ASC" if order == "asc" else "DESC"
        effective_limit = limit if limit is not None else max(total - skip, 0)

        query = f"""
            SELECT * FROM (
                SELECT id, titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido, 
                       categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
                       cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
                       tipo_contenido, created_at
                FROM noticias_limpia
                WHERE {where_clause}
                UNION ALL
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
                WHERE {where_clause}
            ) AS combined_news
            ORDER BY fecha {order_sql} NULLS LAST, id {order_sql}
            OFFSET %s LIMIT %s
        """
        
        cur.execute(query, params + params + [skip, effective_limit])
        rows = cur.fetchall()
        items = [_row_to_news(r) for r in rows]
        return NewsListResponse(total=total, items=items)
    finally:
        put_conn(conn)


@router.get("/categorias/{categoria_name}", response_model=NewsListResponse)
def get_news_by_categoria(
    categoria_name: str,
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1),
    order: str = Query("desc", regex="^(asc|desc)$"),
    fecha_desde: str = Query(None, description="Fecha desde (YYYY-MM-DD)"),
):
    """Obtiene todas las noticias de una categoría específica"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Construir query con filtro de fecha
        where_clause = "categoria = %s"
        params = [categoria_name]
        
        if fecha_desde:
            where_clause += " AND fecha >= %s"
            params.append(fecha_desde)
        
        # Count
        cur.execute(
            f"SELECT COUNT(*) FROM noticias_limpia WHERE {where_clause}",
            params
        )
        total = cur.fetchone()[0]
        
        # Data
        order_sql = "ASC" if order == "asc" else "DESC"
        effective_limit = limit if limit is not None else max(total - skip, 0)

        cur.execute(
            f"""
            SELECT id, titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido, 
                   categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
                   cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
                   tipo_contenido, created_at
            FROM noticias_limpia
            WHERE {where_clause}
            ORDER BY fecha {order_sql} NULLS LAST, id {order_sql}
            OFFSET %s LIMIT %s
            """,
            params + [skip, effective_limit],
        )
        rows = cur.fetchall()
        items = [_row_to_news(r) for r in rows]
        return NewsListResponse(total=total, items=items)
    finally:
        put_conn(conn)

