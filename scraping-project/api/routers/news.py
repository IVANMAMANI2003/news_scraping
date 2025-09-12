from datetime import datetime
from typing import Any, Optional

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
        resumen,
        contenido,
        categoria,
        autor,
        tags,
        url,
        fecha_extraccion,
        imagenes,
        fuente,
        created_at,
    ) = row
    return News(
        id=id,
        titulo=titulo,
        fecha=fecha,
        hora=hora,
        resumen=resumen,
        contenido=contenido,
        categoria=categoria,
        autor=autor,
        tags=tags,
        url=url,
        fecha_extraccion=fecha_extraccion,
        imagenes=imagenes,
        fuente=fuente,
        created_at=created_at,
    )


@router.get("", response_model=NewsListResponse)
def list_news(
    q: Optional[str] = Query(None, description="Texto a buscar en título o contenido"),
    categoria: Optional[str] = Query(None),
    fuente: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    order: str = Query("desc", regex="^(asc|desc)$"),
):
    conn = get_conn()
    try:
        cur = conn.cursor()
        where = []
        params: list[Any] = []

        if q:
            where.append("(titulo ILIKE %s OR contenido ILIKE %s)")
            like = f"%{q}%"
            params.extend([like, like])
        if categoria:
            where.append("categoria = %s")
            params.append(categoria)
        if fuente:
            where.append("fuente = %s")
            params.append(fuente)
        if date_from:
            where.append("fecha >= %s")
            params.append(datetime.strptime(date_from, "%Y-%m-%d"))
        if date_to:
            where.append("fecha <= %s")
            params.append(datetime.strptime(date_to, "%Y-%m-%d"))

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        # Count
        cur.execute(f"SELECT COUNT(*) FROM noticias {where_sql}", params)
        total = cur.fetchone()[0]

        # Data
        order_sql = "ASC" if order == "asc" else "DESC"
        cur.execute(
            f"""
            SELECT id, titulo, fecha, hora, resumen, contenido, categoria, autor,
                   tags, url, fecha_extraccion, imagenes, fuente, created_at
            FROM noticias
            {where_sql}
            ORDER BY fecha {order_sql} NULLS LAST, id {order_sql}
            OFFSET %s LIMIT %s
            """,
            params + [skip, limit],
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
            SELECT id, titulo, fecha, hora, resumen, contenido, categoria, autor,
                   tags, url, fecha_extraccion, imagenes, fuente, created_at
            FROM noticias WHERE id = %s
            """,
            [news_id],
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Noticia no encontrada")
        return _row_to_news(row)
    finally:
        put_conn(conn)

