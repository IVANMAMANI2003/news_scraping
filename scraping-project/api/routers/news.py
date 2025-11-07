from datetime import datetime
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

        # Count
        cur.execute(f"SELECT COUNT(*) FROM noticias_limpia {where_sql}", params)
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
            {where_sql}
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
    """Obtiene la lista de todas las fuentes disponibles"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT fuente FROM noticias_limpia 
            WHERE fuente IS NOT NULL AND fuente != ''
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
    """Obtiene todas las noticias de una fuente específica"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Construir query con filtro de fecha
        where_clause = "fuente = %s"
        params = [fuente_name]
        
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

