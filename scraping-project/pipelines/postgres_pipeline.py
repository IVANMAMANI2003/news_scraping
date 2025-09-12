import logging
from datetime import datetime

import psycopg2
from itemadapter import ItemAdapter
from psycopg2.extras import RealDictCursor


class PostgresPipeline:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def open_spider(self, spider):
        """Abre la conexión a PostgreSQL cuando inicia el spider"""
        try:
            # Configuración de la base de datos
            self.connection = psycopg2.connect(
                host="localhost",
                database="noticias",
                user="root",
                password="123456",  # Cambia por tu contraseña
                port="5432"
            )
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            spider.logger.info("Conexión a PostgreSQL establecida correctamente")
            
            # Crear tabla si no existe
            self.create_table()
            
        except Exception as e:
            spider.logger.error(f"Error al conectar con PostgreSQL: {e}")
            raise

    def create_table(self):
        """Crea la tabla de noticias si no existe"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS noticias (
            id SERIAL PRIMARY KEY,
            titulo TEXT,
            fecha TIMESTAMP,
            resumen TEXT,
            contenido TEXT,
            categoria VARCHAR(100),
            autor VARCHAR(200),
            tags TEXT,
            url TEXT UNIQUE,
            fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            caracteres_contenido INTEGER,
            palabras_contenido INTEGER,
            imagenes TEXT,
            fuente VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            self.cursor.execute(create_table_query)
            self.connection.commit()
            print("Tabla 'noticias' creada o verificada correctamente")
        except Exception as e:
            print(f"Error al crear tabla: {e}")
            raise

    def process_item(self, item, spider):
        """Procesa cada item y lo guarda en PostgreSQL"""
        adapter = ItemAdapter(item)
        
        try:
            # Verificar si la URL ya existe
            check_query = "SELECT id FROM noticias WHERE url = %s"
            self.cursor.execute(check_query, (adapter.get('url'),))
            existing_record = self.cursor.fetchone()
            
            if existing_record:
                spider.logger.info(f"Noticia ya existe en BD: {adapter.get('url')}")
                return item
            
            # Insertar nueva noticia
            insert_query = """
            INSERT INTO noticias (
                titulo, fecha, resumen, contenido, categoria, autor, 
                tags, url, fecha_extraccion, caracteres_contenido, 
                palabras_contenido, imagenes, fuente
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            values = (
                adapter.get('titulo'),
                adapter.get('fecha'),
                adapter.get('resumen'),
                adapter.get('contenido'),
                adapter.get('categoria'),
                adapter.get('autor'),
                adapter.get('tags'),
                adapter.get('url'),
                adapter.get('fecha_extraccion'),
                adapter.get('caracteres_contenido'),
                adapter.get('palabras_contenido'),
                adapter.get('imagenes'),
                adapter.get('fuente')
            )
            
            self.cursor.execute(insert_query, values)
            self.connection.commit()
            
            spider.logger.info(f"Noticia guardada en BD: {adapter.get('titulo')}")
            
        except Exception as e:
            spider.logger.error(f"Error al guardar noticia en BD: {e}")
            self.connection.rollback()
            raise
            
        return item

    def close_spider(self, spider):
        """Cierra la conexión cuando termina el spider"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        spider.logger.info("Conexión a PostgreSQL cerrada")
