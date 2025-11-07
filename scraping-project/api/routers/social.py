from datetime import datetime
from typing import Any, Optional

import feedparser  # type: ignore
from fastapi import APIRouter, HTTPException, Query

from ..db import get_conn, put_conn

router = APIRouter()


SOCIAL_SOURCES = [
    {
        "name": "Reddit r/worldnews",
        "type": "rss",
        "url": "https://www.reddit.com/r/worldnews/.rss",
        "fuente": "Reddit",
        "categoria": "Social",
    },
]


def ensure_table_exists(conn) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS social_news (
            id SERIAL PRIMARY KEY,
            fuente TEXT,
            categoria TEXT,
            titulo TEXT,
            resumen TEXT,
            url TEXT UNIQUE,
            imagen TEXT,
            fecha TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
    )
    conn.commit()


def upsert_post(conn, post: dict[str, Any]) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO social_news (fuente, categoria, titulo, resumen, url, imagen, fecha)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET
            titulo = EXCLUDED.titulo,
            resumen = EXCLUDED.resumen,
            imagen = EXCLUDED.imagen,
            fecha = EXCLUDED.fecha
        """,
        [
            post.get("fuente"),
            post.get("categoria"),
            post.get("titulo"),
            post.get("resumen"),
            post.get("url"),
            post.get("imagen"),
            post.get("fecha"),
        ],
    )


@router.post("/scrape", summary="Extrae posts desde fuentes sociales predefinidas")
def scrape_social():
    conn = get_conn()
    try:
        ensure_table_exists(conn)
        inserted = 0
        for src in SOCIAL_SOURCES:
            if src.get("type") != "rss":
                continue
            feed = feedparser.parse(src["url"])  # type: ignore
            for entry in feed.entries[:50]:  # limitar
                titulo = entry.get("title")
                link = entry.get("link")
                if not link:
                    continue
                resumen = entry.get("summary") or entry.get("description")
                published = entry.get("published") or entry.get("updated")
                fecha: Optional[datetime] = None
                try:
                    if published:
                        fecha = datetime(*entry.published_parsed[:6])  # type: ignore[attr-defined]
                except Exception:
                    fecha = None
                imagen = None
                # Intento simple de extraer media
                media = entry.get("media_content") or entry.get("media_thumbnail")
                if media and isinstance(media, list) and media[0].get("url"):
                    imagen = media[0]["url"]

                post = {
                    "fuente": src["fuente"],
                    "categoria": src["categoria"],
                    "titulo": titulo,
                    "resumen": resumen,
                    "url": link,
                    "imagen": imagen,
                    "fecha": fecha,
                }
                upsert_post(conn, post)
                inserted += 1
        conn.commit()
        return {"status": "ok", "inserted": inserted}
    finally:
        put_conn(conn)


@router.get("/news")
def list_social_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    order: str = Query("desc", regex="^(asc|desc)$"),
):
    conn = get_conn()
    try:
        ensure_table_exists(conn)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM social_news")
        total = cur.fetchone()[0]
        order_sql = "ASC" if order == "asc" else "DESC"
        cur.execute(
            f"""
            SELECT id, fuente, categoria, titulo, resumen, url, imagen, fecha, created_at
            FROM social_news
            ORDER BY fecha {order_sql} NULLS LAST, id {order_sql}
            OFFSET %s LIMIT %s
            """,
            [skip, limit],
        )
        rows = cur.fetchall()
        items = [
            {
                "id": r[0],
                "fuente": r[1],
                "categoria": r[2],
                "titulo": r[3],
                "resumen": r[4],
                "url": r[5],
                "imagen": r[6],
                "fecha": r[7],
                "created_at": r[8],
            }
            for r in rows
        ]
        return {"total": total, "items": items}
    finally:
        put_conn(conn)


