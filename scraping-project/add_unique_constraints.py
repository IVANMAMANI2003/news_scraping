from __future__ import annotations

"""
Add UNIQUE constraints to ensure only-new inserts:
- noticias_limpia.url UNIQUE (if table/column exist)
- social_news.url already UNIQUE in router, kept here for idempotence
"""

from api.db import get_conn, put_conn  # type: ignore


def add_constraints() -> None:
    conn = get_conn()
    try:
        cur = conn.cursor()

        # Ensure social_news exists and unique on url
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

        # Add unique index on noticias_limpia.url if present
        cur.execute(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='noticias_limpia' AND column_name='url'
                ) THEN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes WHERE indexname = 'ux_noticias_limpia_url'
                    ) THEN
                        EXECUTE 'CREATE UNIQUE INDEX ux_noticias_limpia_url ON noticias_limpia(url)';
                    END IF;
                END IF;
            END$$;
            """
        )

        conn.commit()
        print("Constraints applied successfully")
    finally:
        put_conn(conn)


if __name__ == "__main__":
    add_constraints()


