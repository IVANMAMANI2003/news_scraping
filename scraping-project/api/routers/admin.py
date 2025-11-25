"""
Router para gestión administrativa (CRUD)
Permite crear, leer, actualizar y eliminar noticias, fuentes y categorías
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..db import get_conn, put_conn

router = APIRouter()


# ==================== MODELOS ====================

class NewsCreate(BaseModel):
    """Modelo para crear una noticia"""
    titulo: str
    fecha: Optional[str] = None
    hora: Optional[str] = None
    resumen: Optional[str] = None
    contenido: Optional[str] = None
    categoria: Optional[str] = None
    autor: Optional[str] = None
    keywords: Optional[str] = None
    url: str
    dominio: Optional[str] = None
    imagen_principal: Optional[str] = None
    cantidad_imagenes: Optional[int] = 0
    tiene_imagenes: Optional[bool] = False
    fuente: Optional[str] = None
    tipo_contenido: Optional[str] = None


class NewsUpdate(BaseModel):
    """Modelo para actualizar una noticia"""
    titulo: Optional[str] = None
    fecha: Optional[str] = None
    hora: Optional[str] = None
    resumen: Optional[str] = None
    contenido: Optional[str] = None
    categoria: Optional[str] = None
    autor: Optional[str] = None
    keywords: Optional[str] = None
    url: Optional[str] = None
    dominio: Optional[str] = None
    imagen_principal: Optional[str] = None
    cantidad_imagenes: Optional[int] = None
    tiene_imagenes: Optional[bool] = None
    fuente: Optional[str] = None
    tipo_contenido: Optional[str] = None


class SourceCreate(BaseModel):
    """Modelo para crear una fuente"""
    nombre: str
    descripcion: Optional[str] = None
    url_base: Optional[str] = None
    activa: Optional[bool] = True


class SourceUpdate(BaseModel):
    """Modelo para actualizar una fuente"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    url_base: Optional[str] = None
    activa: Optional[bool] = None


class CategoryCreate(BaseModel):
    """Modelo para crear una categoría"""
    nombre: str
    descripcion: Optional[str] = None
    activa: Optional[bool] = True


class CategoryUpdate(BaseModel):
    """Modelo para actualizar una categoría"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activa: Optional[bool] = None


# ==================== NOTICIAS CRUD ====================

@router.post("/admin/news", status_code=201)
def create_news(news: NewsCreate):
    """Crear una nueva noticia"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Validar que la URL no exista
        cur.execute("SELECT id FROM noticias_limpia WHERE url = %s", (news.url,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Ya existe una noticia con esta URL")
        
        # Preparar fecha
        fecha_val = None
        if news.fecha:
            try:
                fecha_val = datetime.strptime(news.fecha, "%Y-%m-%d").date()
            except:
                pass
        
        # Preparar hora
        hora_val = None
        if news.hora:
            try:
                hora_val = datetime.strptime(news.hora, "%H:%M:%S").time()
            except:
                try:
                    hora_val = datetime.strptime(news.hora, "%H:%M").time()
                except:
                    pass
        
        # Calcular campos derivados
        longitud_titulo = len(news.titulo) if news.titulo else 0
        longitud_resumen = len(news.resumen) if news.resumen else 0.0
        
        # Extraer año, mes, día si hay fecha
        anio = fecha_val.year if fecha_val else None
        mes = fecha_val.month if fecha_val else None
        dia = fecha_val.day if fecha_val else None
        
        # Extraer día de la semana
        dia_semana = None
        if fecha_val:
            dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            dia_semana = dias[fecha_val.weekday()]
        
        # Insertar
        insert_query = """
        INSERT INTO noticias_limpia (
            titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido,
            categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
            cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
            tipo_contenido
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
        """
        
        cur.execute(insert_query, (
            news.titulo,
            fecha_val,
            hora_val,
            anio,
            mes,
            dia,
            dia_semana,
            news.resumen,
            news.contenido,
            news.categoria,
            news.autor,
            news.keywords,
            news.url,
            news.dominio,
            datetime.now(),
            news.imagen_principal,
            news.cantidad_imagenes or 0,
            news.tiene_imagenes or False,
            news.fuente,
            longitud_titulo,
            longitud_resumen,
            news.tipo_contenido
        ))
        
        new_id = cur.fetchone()[0]
        conn.commit()
        
        return {"id": new_id, "message": "Noticia creada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando noticia: {str(e)}")
    finally:
        put_conn(conn)


@router.put("/admin/news/{news_id}")
def update_news(news_id: int, news: NewsUpdate):
    """Actualizar una noticia existente"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Verificar que existe
        cur.execute("SELECT id FROM noticias_limpia WHERE id = %s", (news_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Noticia no encontrada")
        
        # Construir query dinámicamente
        updates = []
        params = []
        
        if news.titulo is not None:
            updates.append("titulo = %s")
            params.append(news.titulo)
        
        if news.fecha is not None:
            fecha_val = None
            if news.fecha:
                try:
                    fecha_val = datetime.strptime(news.fecha, "%Y-%m-%d").date()
                except:
                    pass
            updates.append("fecha = %s")
            params.append(fecha_val)
            
            # Actualizar campos derivados de fecha
            if fecha_val:
                updates.append("anio = %s")
                params.append(fecha_val.year)
                updates.append("mes = %s")
                params.append(fecha_val.month)
                updates.append("dia = %s")
                params.append(fecha_val.day)
                dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                updates.append("dia_semana = %s")
                params.append(dias[fecha_val.weekday()])
            else:
                updates.append("anio = %s")
                params.append(None)
                updates.append("mes = %s")
                params.append(None)
                updates.append("dia = %s")
                params.append(None)
                updates.append("dia_semana = %s")
                params.append(None)
        
        if news.hora is not None:
            hora_val = None
            if news.hora:
                try:
                    hora_val = datetime.strptime(news.hora, "%H:%M:%S").time()
                except:
                    try:
                        hora_val = datetime.strptime(news.hora, "%H:%M").time()
                    except:
                        pass
            updates.append("hora = %s")
            params.append(hora_val)
        
        if news.resumen is not None:
            updates.append("resumen = %s")
            params.append(news.resumen)
            updates.append("longitud_resumen = %s")
            params.append(len(news.resumen) if news.resumen else 0.0)
        
        if news.contenido is not None:
            updates.append("contenido = %s")
            params.append(news.contenido)
        
        if news.categoria is not None:
            updates.append("categoria = %s")
            params.append(news.categoria)
        
        if news.autor is not None:
            updates.append("autor = %s")
            params.append(news.autor)
        
        if news.keywords is not None:
            updates.append("keywords = %s")
            params.append(news.keywords)
        
        if news.url is not None:
            # Verificar que la nueva URL no exista en otro registro
            cur.execute("SELECT id FROM noticias_limpia WHERE url = %s AND id != %s", (news.url, news_id))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Ya existe otra noticia con esta URL")
            updates.append("url = %s")
            params.append(news.url)
        
        if news.dominio is not None:
            updates.append("dominio = %s")
            params.append(news.dominio)
        
        if news.imagen_principal is not None:
            updates.append("imagen_principal = %s")
            params.append(news.imagen_principal)
        
        if news.cantidad_imagenes is not None:
            updates.append("cantidad_imagenes = %s")
            params.append(news.cantidad_imagenes)
        
        if news.tiene_imagenes is not None:
            updates.append("tiene_imagenes = %s")
            params.append(news.tiene_imagenes)
        
        if news.fuente is not None:
            updates.append("fuente = %s")
            params.append(news.fuente)
        
        if news.tipo_contenido is not None:
            updates.append("tipo_contenido = %s")
            params.append(news.tipo_contenido)
        
        if news.titulo is not None:
            updates.append("longitud_titulo = %s")
            params.append(len(news.titulo) if news.titulo else 0)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        params.append(news_id)
        
        update_query = f"UPDATE noticias_limpia SET {', '.join(updates)} WHERE id = %s"
        cur.execute(update_query, params)
        conn.commit()
        
        return {"message": "Noticia actualizada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando noticia: {str(e)}")
    finally:
        put_conn(conn)


@router.delete("/admin/news/{news_id}")
def delete_news(news_id: int):
    """Eliminar una noticia"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # Verificar que existe
        cur.execute("SELECT id FROM noticias_limpia WHERE id = %s", (news_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Noticia no encontrada")
        
        cur.execute("DELETE FROM noticias_limpia WHERE id = %s", (news_id,))
        conn.commit()
        
        return {"message": "Noticia eliminada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando noticia: {str(e)}")
    finally:
        put_conn(conn)


# ==================== FUENTES CRUD ====================

@router.get("/admin/sources")
def list_sources():
    """Listar todas las fuentes únicas de noticias_limpia y social_news"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT fuente, SUM(total_noticias) as total_noticias
            FROM (
                SELECT fuente, COUNT(*) as total_noticias
                FROM noticias_limpia
                WHERE fuente IS NOT NULL AND fuente != ''
                GROUP BY fuente
                UNION ALL
                SELECT fuente, COUNT(*) as total_noticias
                FROM social_news
                WHERE fuente IS NOT NULL AND fuente != ''
                GROUP BY fuente
            ) AS combined_sources
            GROUP BY fuente
            ORDER BY fuente
        """)
        rows = cur.fetchall()
        return [
            {"nombre": row[0], "total_noticias": row[1]}
            for row in rows
        ]
    finally:
        put_conn(conn)


@router.post("/admin/sources")
def create_source(source: SourceCreate):
    """Crear una nueva fuente (actualiza noticias existentes)"""
    # Las fuentes se manejan como valores en la columna 'fuente'
    # No hay tabla separada, así que solo validamos
    return {
        "nombre": source.nombre,
        "message": "Fuente registrada. Se aplicará a nuevas noticias."
    }


@router.put("/admin/sources/{old_name}")
def update_source(old_name: str, source: SourceUpdate):
    """Actualizar nombre de fuente (actualiza todas las noticias con esa fuente)"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        if not source.nombre:
            raise HTTPException(status_code=400, detail="El nuevo nombre es requerido")
        
        # Actualizar todas las noticias con la fuente antigua
        cur.execute("""
            UPDATE noticias_limpia
            SET fuente = %s
            WHERE fuente = %s
        """, (source.nombre, old_name))
        
        affected = cur.rowcount
        conn.commit()
        
        return {
            "message": f"Fuente actualizada. {affected} noticia(s) actualizada(s).",
            "nombre_anterior": old_name,
            "nombre_nuevo": source.nombre
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando fuente: {str(e)}")
    finally:
        put_conn(conn)


@router.delete("/admin/sources/{source_name}")
def delete_source(source_name: str):
    """Eliminar fuente (establece fuente a NULL en todas las noticias)"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE noticias_limpia
            SET fuente = NULL
            WHERE fuente = %s
        """, (source_name,))
        
        affected = cur.rowcount
        conn.commit()
        
        return {
            "message": f"Fuente eliminada. {affected} noticia(s) actualizada(s)."
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando fuente: {str(e)}")
    finally:
        put_conn(conn)


# ==================== CATEGORÍAS CRUD ====================

@router.get("/admin/categories")
def list_categories():
    """Listar todas las categorías únicas"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT categoria, COUNT(*) as total_noticias
            FROM noticias_limpia
            WHERE categoria IS NOT NULL AND categoria != ''
            GROUP BY categoria
            ORDER BY categoria
        """)
        rows = cur.fetchall()
        return [
            {"nombre": row[0], "total_noticias": row[1]}
            for row in rows
        ]
    finally:
        put_conn(conn)


@router.post("/admin/categories")
def create_category(category: CategoryCreate):
    """Crear una nueva categoría (solo registro, se aplica a nuevas noticias)"""
    return {
        "nombre": category.nombre,
        "message": "Categoría registrada. Se aplicará a nuevas noticias."
    }


@router.put("/admin/categories/{old_name}")
def update_category(old_name: str, category: CategoryUpdate):
    """Actualizar nombre de categoría (actualiza todas las noticias con esa categoría)"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        if not category.nombre:
            raise HTTPException(status_code=400, detail="El nuevo nombre es requerido")
        
        # Actualizar todas las noticias con la categoría antigua
        cur.execute("""
            UPDATE noticias_limpia
            SET categoria = %s
            WHERE categoria = %s
        """, (category.nombre, old_name))
        
        affected = cur.rowcount
        conn.commit()
        
        return {
            "message": f"Categoría actualizada. {affected} noticia(s) actualizada(s).",
            "nombre_anterior": old_name,
            "nombre_nuevo": category.nombre
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error actualizando categoría: {str(e)}")
    finally:
        put_conn(conn)


@router.delete("/admin/categories/{category_name}")
def delete_category(category_name: str):
    """Eliminar categoría (establece categoría a NULL en todas las noticias)"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE noticias_limpia
            SET categoria = NULL
            WHERE categoria = %s
        """, (category_name,))
        
        affected = cur.rowcount
        conn.commit()
        
        return {
            "message": f"Categoría eliminada. {affected} noticia(s) actualizada(s)."
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error eliminando categoría: {str(e)}")
    finally:
        put_conn(conn)

