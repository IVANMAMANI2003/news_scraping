import glob
import os

import pandas as pd
import psycopg2

DB_CONFIG = {
    "host": "db",
    "dbname": "newsdb",
    "user": "postgres",
    "password": "postgres",
    "port": 5432
}

def migrate_csv_to_postgres():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    files = glob.glob("data/*.csv")
    for file in files:
        df = pd.read_csv(file)

        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO articles 
                (titulo, fecha, resumen, contenido, categoria, autor, tag, url, fecha_extraccion, caracteres_contenido, palabras_contenido, imagenes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (url) DO NOTHING;
            """, (
                row.get("titulo"),
                row.get("fecha"),
                row.get("resumen"),
                row.get("contenido"),
                row.get("categoria"),
                row.get("autor"),
                row.get("tag"),
                row.get("url"),
                row.get("fecha_extraccion"),
                row.get("caracteres_contenido"),
                row.get("palabras_contenido"),
                row.get("imagenes"),
            ))
        print(f"Migrado: {file}")
        conn.commit()

    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate_csv_to_postgres()
