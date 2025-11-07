from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from typing import Any

import psycopg2


def get_db_conn():
    host = os.getenv("PGHOST", "127.0.0.1")
    port = int(os.getenv("PGPORT", "5432"))
    db = os.getenv("PGDATABASE", "noticias")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "123456")
    return psycopg2.connect(host=host, port=port, dbname=db, user=user, password=password)


def ensure_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS noticias (
            id SERIAL PRIMARY KEY,
            titulo TEXT,
            fecha TIMESTAMP NULL,
            resumen TEXT,
            contenido TEXT,
            categoria VARCHAR(100),
            autor VARCHAR(200),
            tags TEXT,
            url TEXT UNIQUE,
            fecha_extraccion TIMESTAMP,
            caracteres_contenido INTEGER,
            palabras_contenido INTEGER,
            imagenes TEXT,
            fuente VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
    )


def load_latest_json(data_dir: Path) -> list[dict[str, Any]]:
    files = sorted(data_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return []
    path = files[0]
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict):
            # some dumps store under 'items'
            data = data.get("items", [])  # type: ignore[assignment]
        if not isinstance(data, list):
            return []
        return data  # type: ignore[return-value]


def upsert_news(cur, item: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO noticias (
            titulo, fecha, resumen, contenido, categoria, autor,
            tags, url, fecha_extraccion, caracteres_contenido,
            palabras_contenido, imagenes, fuente
        ) VALUES (
            %(titulo)s, %(fecha)s, %(resumen)s, %(contenido)s, %(categoria)s, %(autor)s,
            %(tags)s, %(url)s, %(fecha_extraccion)s, %(caracteres_contenido)s,
            %(palabras_contenido)s, %(imagenes)s, %(fuente)s
        ) ON CONFLICT (url) DO NOTHING
        """,
        item,
    )


def main() -> None:
    data_dir = Path("data/pachamamaradio")
    items = load_latest_json(data_dir)
    if not items:
        print("No se encontraron archivos JSON recientes para pachamamaradio")
        return

    conn = get_db_conn()
    try:
        cur = conn.cursor()
        ensure_table(cur)
        inserted = 0
        for raw in items:
            try:
                upsert_news(cur, raw)
                inserted += 1
            except Exception:
                # saltar registros problemáticos
                conn.rollback()
                continue
        conn.commit()
        print(f"Migración pachamamaradio completada. Insertados: {inserted}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


