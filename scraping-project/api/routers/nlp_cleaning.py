"""
Router para limpieza de noticias usando Ollama
Permite limpiar noticias con diferentes filtros desde el panel de admin
"""

import json
import logging
import os
import sys
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

# Agregar el directorio nlp_cleaning al path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'nlp_cleaning'))

try:
    from nlp_cleaner import NLPContentCleaner, clean_news
except ImportError:
    # Si no se encuentra, intentar desde el directorio padre
    nlp_cleaning_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'nlp_cleaning')
    if os.path.exists(nlp_cleaning_path):
        sys.path.insert(0, nlp_cleaning_path)
        from nlp_cleaner import NLPContentCleaner, clean_news
    else:
        clean_news = None
        NLPContentCleaner = None

from ..auth import require_role
from ..db import get_conn, put_conn

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== MODELOS ====================

class LimpiezaRequest(BaseModel):
    """Modelo para solicitud de limpieza"""
    noticia_id: Optional[int] = None
    titulo: Optional[str] = None
    categoria: Optional[str] = None
    fuente: Optional[str] = None
    cantidad: Optional[int] = None
    fecha_desde: Optional[str] = None
    fecha_hasta: Optional[str] = None
    prompt_personalizado: Optional[str] = None
    modelo: Optional[str] = "deepseek-r1:8b"
    tabla_origen: Optional[str] = "noticias"


class LimpiezaResponse(BaseModel):
    """Modelo para respuesta de limpieza"""
    procesadas: int
    exitosas: int
    errores: int
    detalles: List[dict]


class NoticiaLimpia(BaseModel):
    """Modelo para noticia limpiada"""
    id: int
    noticia_id: Optional[int] = None
    titulo: str
    resumen: Optional[str] = None
    contenido_limpio: Optional[str] = None
    num_parrafos_total: Optional[int] = None
    num_parrafos_relevantes: Optional[int] = None
    num_parrafos_irrelevantes: Optional[int] = None
    url: Optional[str] = None
    fuente: Optional[str] = None
    fecha: Optional[str] = None
    modelo_usado: Optional[str] = None
    procesado_at: Optional[str] = None
    porcentaje_relevancia: Optional[float] = None


class NoticiaLimpiaDetalle(NoticiaLimpia):
    """Modelo para noticia limpiada con detalles completos"""
    contenido_raw: Optional[str] = None
    parrafos_relevantes: Optional[List[str]] = None
    parrafos_irrelevantes: Optional[List[str]] = None


class NoticiasLimpiadasResponse(BaseModel):
    """Respuesta de lista de noticias limpiadas"""
    total: int
    items: List[NoticiaLimpia]


class NewsIA(BaseModel):
    """Modelo para noticia procesada con IA (vista pública)"""
    # ID de noticias_bert_clean
    bert_clean_id: int
    
    # Datos de noticias_limpia (obtenidos a través de foreign key)
    noticia_id: int
    titulo: str
    resumen: Optional[str] = None
    contenido_original: Optional[str] = None
    categoria: Optional[str] = None
    autor: Optional[str] = None
    keywords: Optional[str] = None
    url: Optional[str] = None
    dominio: Optional[str] = None
    fecha: Optional[str] = None
    hora: Optional[str] = None
    fuente: Optional[str] = None
    imagen_principal: Optional[str] = None
    cantidad_imagenes: Optional[int] = None
    tiene_imagenes: Optional[bool] = None
    
    # Datos de noticias_bert_clean
    contenido_limpio: Optional[str] = None
    parrafos_relevantes: Optional[List[str]] = None
    parrafos_irrelevantes: Optional[List[str]] = None
    num_parrafos_total: Optional[int] = None
    num_parrafos_relevantes: Optional[int] = None
    num_parrafos_irrelevantes: Optional[int] = None
    modelo_usado: Optional[str] = None
    procesado_at: Optional[str] = None
    
    # Campos calculados
    porcentaje_relevancia: Optional[float] = None


class NewsIAListResponse(BaseModel):
    """Respuesta de lista de noticias procesadas con IA"""
    total: int
    items: List[NewsIA]


# ==================== ENDPOINTS ====================

@router.post("/nlp/limpiar", response_model=LimpiezaResponse)
async def limpiar_noticias(request: LimpiezaRequest):
    """
    Limpia noticias usando Ollama con diferentes filtros.
    
    Filtros disponibles:
    - noticia_id: Limpiar una noticia específica
    - categoria: Limpiar noticias de una categoría
    - fuente: Limpiar noticias de una fuente
    - cantidad: Limpiar un número específico de noticias
    - fecha_desde/fecha_hasta: Filtrar por rango de fechas
    - prompt_personalizado: Usar un prompt personalizado
    """
    if clean_news is None:
        raise HTTPException(
            status_code=503,
            detail="Módulo de limpieza NLP no disponible. Verifica que nlp_cleaning esté instalado."
        )
    
    conn = get_conn()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    try:
        cursor = conn.cursor()
        
        # Construir query según filtros
        query = f"SELECT id, titulo, resumen, contenido, url, fuente, fecha FROM {request.tabla_origen} WHERE 1=1"
        params = []
        
        if request.noticia_id:
            query += " AND id = %s"
            params.append(request.noticia_id)
        
        if request.titulo:
            query += " AND titulo ILIKE %s"
            params.append(f"%{request.titulo}%")
        
        if request.categoria:
            query += " AND categoria = %s"
            params.append(request.categoria)
        
        if request.fuente:
            query += " AND fuente = %s"
            params.append(request.fuente)
        
        if request.fecha_desde:
            query += " AND fecha >= %s"
            params.append(request.fecha_desde)
        
        if request.fecha_hasta:
            query += " AND fecha <= %s"
            params.append(request.fecha_hasta)
        
        # Ordenar por fecha descendente
        query += " ORDER BY fecha DESC"
        
        # Limitar cantidad si se especifica
        if request.cantidad:
            query += " LIMIT %s"
            params.append(request.cantidad)
        
        cursor.execute(query, params)
        noticias = cursor.fetchall()
        
        if not noticias:
            return LimpiezaResponse(
                procesadas=0,
                exitosas=0,
                errores=0,
                detalles=[]
            )
        
        logger.info(f"📊 Procesando {len(noticias)} noticias con filtros")
        
        # Inicializar limpiador con prompt personalizado si se proporciona
        if request.prompt_personalizado:
            # Crear un limpiador personalizado (esto requeriría modificar la clase)
            cleaner = NLPContentCleaner(model_name=request.modelo)
            # Por ahora, usamos el limpiador estándar
            # TODO: Implementar prompt personalizado
            logger.info("⚠️ Prompt personalizado aún no implementado, usando prompt estándar")
        
        # Procesar noticias
        exitosas = 0
        errores = 0
        detalles = []
        
        for noticia in noticias:
            noticia_id, titulo, resumen, contenido, url, fuente, fecha = noticia
            
            try:
                # Limpiar contenido
                result = clean_news(
                    title=titulo or "",
                    summary=resumen or "",
                    raw=contenido or "",
                    model_name=request.modelo
                )
                
                # Validar y obtener noticia_id
                final_noticia_id = None
                
                # Si hay noticia_id, validar que existe en noticias_limpia
                if noticia_id:
                    try:
                        cursor.execute("""
                            SELECT id FROM noticias_limpia WHERE id = %s LIMIT 1
                        """, (noticia_id,))
                        result_id = cursor.fetchone()
                        if result_id:
                            final_noticia_id = noticia_id
                        else:
                            logger.warning(f"⚠️ noticia_id {noticia_id} no existe en noticias_limpia, intentando buscar por URL")
                            # Si no existe, intentar buscar por URL
                            if url:
                                cursor.execute("""
                                    SELECT id FROM noticias_limpia WHERE url = %s LIMIT 1
                                """, (url,))
                                result_id = cursor.fetchone()
                                if result_id:
                                    final_noticia_id = result_id[0]
                                    logger.info(f"✅ Encontrado noticia_id {final_noticia_id} por URL para noticia {noticia_id}")
                    except Exception as e:
                        logger.error(f"❌ Error validando noticia_id {noticia_id}: {e}")
                        # Si falla, intentar buscar por URL
                        if url:
                            try:
                                cursor.execute("""
                                    SELECT id FROM noticias_limpia WHERE url = %s LIMIT 1
                                """, (url,))
                                result_id = cursor.fetchone()
                                if result_id:
                                    final_noticia_id = result_id[0]
                            except Exception:
                                pass
                
                # Si aún no hay noticia_id y hay URL, intentar obtenerlo de noticias_limpia basándose en URL
                if not final_noticia_id and url:
                    try:
                        cursor.execute("""
                            SELECT id FROM noticias_limpia WHERE url = %s LIMIT 1
                        """, (url,))
                        result_id = cursor.fetchone()
                        if result_id:
                            final_noticia_id = result_id[0]
                    except Exception:
                        pass  # Si falla, usar NULL
                
                # Si no se encontró noticia_id válido, usar NULL (permitido por la foreign key si es nullable)
                if not final_noticia_id:
                    logger.warning(f"⚠️ No se encontró noticia_id válido para noticia {noticia_id} (URL: {url}). Usando NULL para noticia_id.")
                
                # Guardar en noticias_bert_clean
                # Verificar si ya existe un registro con esta URL
                if url:
                    cursor.execute("""
                        SELECT id FROM noticias_bert_clean WHERE url = %s LIMIT 1
                    """, (url,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Actualizar registro existente
                        # Solo actualizar noticia_id si tenemos uno válido, de lo contrario mantener el existente
                        update_query = """
                            UPDATE noticias_bert_clean SET
                                noticia_id = COALESCE(%s, noticia_id),
                                titulo = %s,
                                resumen = %s,
                                contenido_raw = %s,
                                contenido_limpio = %s,
                                parrafos_relevantes = %s,
                                parrafos_irrelevantes = %s,
                                num_parrafos_total = %s,
                                num_parrafos_relevantes = %s,
                                num_parrafos_irrelevantes = %s,
                                fuente = COALESCE(%s, fuente),
                                fecha = COALESCE(%s, fecha),
                                modelo_usado = %s,
                                procesado_at = CURRENT_TIMESTAMP
                            WHERE url = %s
                        """
                        cursor.execute(update_query, (
                            final_noticia_id,
                            titulo,
                            resumen,
                            contenido,
                            result.get('clean_text', ''),
                            json.dumps(result.get('relevantes', [])),
                            json.dumps(result.get('irrelevantes', [])),
                            len(result.get('relevantes', [])) + len(result.get('irrelevantes', [])),
                            len(result.get('relevantes', [])),
                            len(result.get('irrelevantes', [])),
                            fuente,
                            fecha,
                            request.modelo,
                            url
                        ))
                    else:
                        # Insertar nuevo registro
                        insert_query = """
                            INSERT INTO noticias_bert_clean (
                                noticia_id, titulo, resumen, contenido_raw, contenido_limpio,
                                parrafos_relevantes, parrafos_irrelevantes,
                                num_parrafos_total, num_parrafos_relevantes, num_parrafos_irrelevantes,
                                url, fuente, fecha, modelo_usado
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """
                        cursor.execute(insert_query, (
                            final_noticia_id,
                            titulo,
                            resumen,
                            contenido,
                            result.get('clean_text', ''),
                            json.dumps(result.get('relevantes', [])),
                            json.dumps(result.get('irrelevantes', [])),
                            len(result.get('relevantes', [])) + len(result.get('irrelevantes', [])),
                            len(result.get('relevantes', [])),
                            len(result.get('irrelevantes', [])),
                            url,
                            fuente,
                            fecha,
                            request.modelo
                        ))
                else:
                    # Si no hay URL, insertar sin verificar duplicados
                    insert_query = """
                        INSERT INTO noticias_bert_clean (
                            noticia_id, titulo, resumen, contenido_raw, contenido_limpio,
                            parrafos_relevantes, parrafos_irrelevantes,
                            num_parrafos_total, num_parrafos_relevantes, num_parrafos_irrelevantes,
                            url, fuente, fecha, modelo_usado
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """
                    cursor.execute(insert_query, (
                        final_noticia_id,
                        titulo,
                        resumen,
                        contenido,
                        result.get('clean_text', ''),
                        json.dumps(result.get('relevantes', [])),
                        json.dumps(result.get('irrelevantes', [])),
                        len(result.get('relevantes', [])) + len(result.get('irrelevantes', [])),
                        len(result.get('relevantes', [])),
                        len(result.get('irrelevantes', [])),
                        url,
                        fuente,
                        fecha,
                        request.modelo
                    ))
                
                # Verificar si hubo algún error de foreign key
                conn.commit()
                
                exitosas += 1
                estado_detalle = "exitoso"
                mensaje_detalle = None
                if not final_noticia_id and noticia_id:
                    estado_detalle = "advertencia"
                    mensaje_detalle = f"Procesada con noticia_id NULL (el ID {noticia_id} no existe en noticias_limpia)"
                
                detalles.append({
                    "noticia_id": noticia_id,
                    "titulo": titulo[:50] + "..." if titulo and len(titulo) > 50 else titulo,
                    "estado": estado_detalle,
                    "relevantes": len(result.get('relevantes', [])),
                    "irrelevantes": len(result.get('irrelevantes', [])),
                    "mensaje": mensaje_detalle
                })
                
            except Exception as e:
                errores += 1
                error_msg = str(e)
                logger.error(f"❌ Error procesando noticia {noticia_id}: {e}")
                
                # Si es un error de foreign key, proporcionar mensaje más claro
                if "viola la llave foránea" in error_msg or "foreign key" in error_msg.lower() or "fk_noticia_limpia" in error_msg:
                    error_msg = f"El noticia_id {noticia_id} no existe en noticias_limpia. Verifica que la noticia exista antes de procesarla."
                    logger.error(f"❌ Foreign key error: {error_msg}")
                
                detalles.append({
                    "noticia_id": noticia_id,
                    "titulo": titulo[:50] + "..." if titulo and len(titulo) > 50 else titulo,
                    "estado": "error",
                    "error": error_msg
                })
                conn.rollback()  # Rollback en caso de error
        
        conn.commit()
        
        return LimpiezaResponse(
            procesadas=len(noticias),
            exitosas=exitosas,
            errores=errores,
            detalles=detalles
        )
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Error en limpieza: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando noticias: {str(e)}")
    finally:
        cursor.close()
        put_conn(conn)


@router.get("/nlp/estadisticas")
async def obtener_estadisticas_limpieza():
    """Obtiene estadísticas de noticias limpiadas"""
    conn = get_conn()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    try:
        cursor = conn.cursor()
        
        # Total de noticias limpiadas
        cursor.execute("SELECT COUNT(*) FROM noticias_bert_clean")
        total_limpiadas = cursor.fetchone()[0]
        
        # Por modelo
        cursor.execute("""
            SELECT modelo_usado, COUNT(*) 
            FROM noticias_bert_clean 
            GROUP BY modelo_usado
        """)
        por_modelo = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Por fuente
        cursor.execute("""
            SELECT fuente, COUNT(*) 
            FROM noticias_bert_clean 
            WHERE fuente IS NOT NULL
            GROUP BY fuente
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        por_fuente = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_limpiadas": total_limpiadas,
            "por_modelo": por_modelo,
            "por_fuente": por_fuente
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")
    finally:
        cursor.close()
        put_conn(conn)


@router.get("/nlp/limpiadas", response_model=NoticiasLimpiadasResponse)
async def listar_noticias_limpiadas(
    fuente: Optional[str] = Query(None, description="Filtrar por fuente"),
    modelo: Optional[str] = Query(None, description="Filtrar por modelo usado"),
    q: Optional[str] = Query(None, description="Búsqueda en título o contenido limpio"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(50, ge=1, le=100),
    order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: dict = Depends(require_role(["admin", "enterprise"]))
):
    """
    Lista las noticias que han sido limpiadas (de la tabla noticias_bert_clean).
    Solo accesible para admin y enterprise.
    """
    conn = get_conn()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    try:
        cursor = conn.cursor()
        
        # Construir WHERE clause
        where_clauses = []
        params = []
        
        if fuente:
            where_clauses.append("fuente = %s")
            params.append(fuente)
        
        if modelo:
            where_clauses.append("modelo_usado = %s")
            params.append(modelo)
        
        if q:
            where_clauses.append("(titulo ILIKE %s OR contenido_limpio ILIKE %s)")
            search_term = f"%{q}%"
            params.extend([search_term, search_term])
        
        if fecha_desde:
            where_clauses.append("fecha >= %s")
            params.append(fecha_desde)
        
        if fecha_hasta:
            where_clauses.append("fecha <= %s")
            params.append(fecha_hasta)
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM noticias_bert_clean {where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Obtener datos
        order_sql = "ASC" if order == "asc" else "DESC"
        effective_limit = limit if limit is not None else max(total - skip, 0)
        
        select_query = f"""
            SELECT 
                id,
                noticia_id,
                titulo,
                resumen,
                contenido_limpio,
                num_parrafos_total,
                num_parrafos_relevantes,
                num_parrafos_irrelevantes,
                url,
                fuente,
                CASE WHEN fecha IS NOT NULL THEN TO_CHAR(fecha, 'YYYY-MM-DD HH24:MI:SS') ELSE NULL END as fecha,
                modelo_usado,
                CASE WHEN procesado_at IS NOT NULL THEN TO_CHAR(procesado_at, 'YYYY-MM-DD HH24:MI:SS') ELSE NULL END as procesado_at,
                CASE 
                    WHEN num_parrafos_total > 0 AND num_parrafos_total IS NOT NULL
                    THEN ROUND((COALESCE(num_parrafos_relevantes, 0)::numeric / num_parrafos_total::numeric) * 100, 2)
                    ELSE 0
                END as porcentaje_relevancia
            FROM noticias_bert_clean
            {where_sql}
            ORDER BY procesado_at {order_sql} NULLS LAST, fecha {order_sql} NULLS LAST
            OFFSET %s LIMIT %s
        """
        
        try:
            cursor.execute(select_query, params + [skip, effective_limit])
            rows = cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Error ejecutando query: {e}")
            logger.error(f"Query: {select_query}")
            logger.error(f"Params: {params + [skip, effective_limit]}")
            raise
        
        # Convertir a modelos
        items = []
        for row in rows:
            try:
                items.append(NoticiaLimpia(
                    id=row[0],
                    noticia_id=row[1],
                    titulo=row[2] or "",
                    resumen=row[3],
                    contenido_limpio=row[4],
                    num_parrafos_total=row[5],
                    num_parrafos_relevantes=row[6],
                    num_parrafos_irrelevantes=row[7],
                    url=row[8],
                    fuente=row[9],
                    fecha=row[10] if row[10] else None,
                    modelo_usado=row[11],
                    procesado_at=row[12] if row[12] else None,
                    porcentaje_relevancia=float(row[13]) if row[13] is not None else None
                ))
            except Exception as e:
                logger.error(f"❌ Error convirtiendo fila a modelo: {e}")
                logger.error(f"Fila: {row}")
                continue
        
        return NoticiasLimpiadasResponse(total=total, items=items)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo noticias limpiadas: {e}", exc_info=True)
        import traceback
        error_detail = f"Error obteniendo noticias: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)
    finally:
        if cursor:
            cursor.close()
        put_conn(conn)


@router.get("/nlp/limpiadas/{noticia_id}", response_model=NoticiaLimpiaDetalle)
async def obtener_noticia_limpiada_detalle(
    noticia_id: int,
    current_user: dict = Depends(require_role(["admin", "enterprise"]))
):
    """
    Obtiene los detalles completos de una noticia limpiada, incluyendo párrafos relevantes e irrelevantes.
    Solo accesible para admin y enterprise.
    """
    conn = get_conn()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    cursor = None
    try:
        cursor = conn.cursor()
        
        select_query = """
            SELECT 
                id,
                noticia_id,
                titulo,
                resumen,
                contenido_raw,
                contenido_limpio,
                parrafos_relevantes,
                parrafos_irrelevantes,
                num_parrafos_total,
                num_parrafos_relevantes,
                num_parrafos_irrelevantes,
                url,
                fuente,
                CASE WHEN fecha IS NOT NULL THEN TO_CHAR(fecha, 'YYYY-MM-DD HH24:MI:SS') ELSE NULL END as fecha,
                modelo_usado,
                CASE WHEN procesado_at IS NOT NULL THEN TO_CHAR(procesado_at, 'YYYY-MM-DD HH24:MI:SS') ELSE NULL END as procesado_at,
                CASE 
                    WHEN num_parrafos_total > 0 AND num_parrafos_total IS NOT NULL
                    THEN ROUND((COALESCE(num_parrafos_relevantes, 0)::numeric / num_parrafos_total::numeric) * 100, 2)
                    ELSE 0
                END as porcentaje_relevancia
            FROM noticias_bert_clean
            WHERE id = %s
        """
        
        cursor.execute(select_query, (noticia_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Noticia limpiada no encontrada")
        
        # Procesar párrafos relevantes e irrelevantes (JSONB)
        parrafos_relevantes = None
        parrafos_irrelevantes = None
        
        if row[6]:  # parrafos_relevantes
            try:
                if isinstance(row[6], str):
                    parrafos_relevantes = json.loads(row[6])
                else:
                    parrafos_relevantes = row[6]
            except (json.JSONDecodeError, TypeError):
                parrafos_relevantes = []
        
        if row[7]:  # parrafos_irrelevantes
            try:
                if isinstance(row[7], str):
                    parrafos_irrelevantes = json.loads(row[7])
                else:
                    parrafos_irrelevantes = row[7]
            except (json.JSONDecodeError, TypeError):
                parrafos_irrelevantes = []
        
        return NoticiaLimpiaDetalle(
            id=row[0],
            noticia_id=row[1],
            titulo=row[2] or "",
            resumen=row[3],
            contenido_raw=row[4],
            contenido_limpio=row[5],
            parrafos_relevantes=parrafos_relevantes,
            parrafos_irrelevantes=parrafos_irrelevantes,
            num_parrafos_total=row[8],
            num_parrafos_relevantes=row[9],
            num_parrafos_irrelevantes=row[10],
            url=row[11],
            fuente=row[12],
            fecha=row[13],
            modelo_usado=row[14],
            procesado_at=row[15],
            porcentaje_relevancia=float(row[16]) if row[16] is not None else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo detalle de noticia limpiada: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error obteniendo detalle: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        put_conn(conn)


@router.get("/nlp/public", response_model=NewsIAListResponse)
async def obtener_noticias_ia_publicas(
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    fuente: Optional[str] = Query(None, description="Filtrar por fuente"),
    q: Optional[str] = Query(None, description="Búsqueda en título, contenido limpio o resumen"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(20, ge=1, le=100),
    order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: Optional[dict] = Depends(require_role(["admin", "user", "moderator"], optional=True))
):
    """
    Obtiene noticias procesadas con IA para el público.
    Requiere autenticación y plan enterprise o premium.
    Admin tiene acceso completo a todo.
    Hace JOIN entre noticias_bert_clean y noticias_limpia usando la foreign key (noticia_id).
    Incluye categoría, autor, keywords y otros datos de noticias_limpia.
    """
    # Verificar que el usuario tenga un plan que permita acceso
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Se requiere autenticación para acceder a las noticias con IA"
        )
    
    user_plan = (current_user.get("plan") or "free").lower()
    user_role = (current_user.get("rol") or "user").lower()
    
    # Admin tiene acceso a todo, enterprise y premium también tienen acceso
    if user_role == "admin":
        # Admin tiene acceso completo, continuar sin restricciones
        pass
    elif user_plan not in ["enterprise", "premium"]:
        raise HTTPException(
            status_code=403,
            detail="Esta funcionalidad solo está disponible para usuarios con plan Enterprise o Premium. Por favor, actualiza tu plan para acceder."
        )
    conn = get_conn()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    try:
        cursor = conn.cursor()
        
        # Construir WHERE clause
        where_clauses = ["nbc.noticia_id IS NOT NULL", "nl.id IS NOT NULL"]  # Solo noticias con relación válida
        params = []
        
        if categoria:
            where_clauses.append("nl.categoria = %s")
            params.append(categoria)
        
        if fuente:
            where_clauses.append("(nl.fuente = %s OR nbc.fuente = %s)")
            params.extend([fuente, fuente])
        
        if q:
            where_clauses.append("(nl.titulo ILIKE %s OR nbc.contenido_limpio ILIKE %s OR nl.resumen ILIKE %s)")
            search_term = f"%{q}%"
            params.extend([search_term, search_term, search_term])
        
        if fecha_desde:
            where_clauses.append("COALESCE(nl.fecha, nbc.fecha) >= %s")
            params.append(fecha_desde)
        
        if fecha_hasta:
            where_clauses.append("COALESCE(nl.fecha, nbc.fecha) <= %s")
            params.append(fecha_hasta)
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Count total
        count_query = f"""
            SELECT COUNT(*)
            FROM noticias_bert_clean nbc
            INNER JOIN noticias_limpia nl ON nbc.noticia_id = nl.id
            {where_sql}
        """
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Obtener datos con JOIN
        order_sql = "ASC" if order == "asc" else "DESC"
        effective_limit = limit if limit is not None else max(total - skip, 0)
        
        select_query = f"""
            SELECT 
                nbc.id as bert_clean_id,
                nl.id as noticia_id,
                COALESCE(nl.titulo, nbc.titulo) as titulo,
                nl.resumen,
                nl.contenido as contenido_original,
                nl.categoria,
                nl.autor,
                nl.keywords,
                COALESCE(nl.url, nbc.url) as url,
                nl.dominio,
                COALESCE(nl.fecha, nbc.fecha)::text as fecha,
                nl.hora::text as hora,
                COALESCE(nl.fuente, nbc.fuente) as fuente,
                nl.imagen_principal,
                nl.cantidad_imagenes,
                nl.tiene_imagenes,
                nbc.contenido_limpio,
                nbc.parrafos_relevantes,
                nbc.parrafos_irrelevantes,
                nbc.num_parrafos_total,
                nbc.num_parrafos_relevantes,
                nbc.num_parrafos_irrelevantes,
                nbc.modelo_usado,
                nbc.procesado_at::text as procesado_at,
                CASE 
                    WHEN nbc.num_parrafos_total > 0 AND nbc.num_parrafos_total IS NOT NULL
                    THEN ROUND((COALESCE(nbc.num_parrafos_relevantes, 0)::numeric / nbc.num_parrafos_total::numeric) * 100, 2)
                    ELSE 0
                END as porcentaje_relevancia
            FROM noticias_bert_clean nbc
            INNER JOIN noticias_limpia nl ON nbc.noticia_id = nl.id
            {where_sql}
            ORDER BY nbc.procesado_at {order_sql}, COALESCE(nl.fecha, nbc.fecha) {order_sql} NULLS LAST
            OFFSET %s LIMIT %s
        """
        
        cursor.execute(select_query, params + [skip, effective_limit])
        rows = cursor.fetchall()
        
        # Convertir a modelos
        items = []
        for row in rows:
            # Parsear JSON de párrafos
            parrafos_relevantes = None
            parrafos_irrelevantes = None
            
            if row[17]:  # parrafos_relevantes
                try:
                    if isinstance(row[17], str):
                        parrafos_relevantes = json.loads(row[17])
                    else:
                        parrafos_relevantes = row[17]
                except:
                    parrafos_relevantes = []
            
            if row[18]:  # parrafos_irrelevantes
                try:
                    if isinstance(row[18], str):
                        parrafos_irrelevantes = json.loads(row[18])
                    else:
                        parrafos_irrelevantes = row[18]
                except:
                    parrafos_irrelevantes = []
            
            items.append(NewsIA(
                bert_clean_id=row[0],
                noticia_id=row[1],
                titulo=row[2] or "",
                resumen=row[3],
                contenido_original=row[4],
                categoria=row[5],
                autor=row[6],
                keywords=row[7],
                url=row[8],
                dominio=row[9],
                fecha=row[10],
                hora=row[11],
                fuente=row[12],
                imagen_principal=row[13],
                cantidad_imagenes=row[14],
                tiene_imagenes=row[15],
                contenido_limpio=row[16],
                parrafos_relevantes=parrafos_relevantes,
                parrafos_irrelevantes=parrafos_irrelevantes,
                num_parrafos_total=row[19],
                num_parrafos_relevantes=row[20],
                num_parrafos_irrelevantes=row[21],
                modelo_usado=row[22],
                procesado_at=row[23],
                porcentaje_relevancia=float(row[24]) if row[24] else None
            ))
        
        return NewsIAListResponse(total=total, items=items)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo noticias IA públicas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo noticias: {str(e)}")
    finally:
        cursor.close()
        put_conn(conn)


@router.get("/nlp/public/{noticia_id}", response_model=NewsIA)
async def obtener_noticia_ia_publica(
    noticia_id: int,
    current_user: Optional[dict] = Depends(require_role(["admin", "user", "moderator"], optional=True))
):
    """
    Obtiene una noticia procesada con IA por ID para el público.
    Requiere autenticación y plan enterprise o premium.
    Admin tiene acceso completo a todo.
    Usa el noticia_id (de noticias_limpia) para buscar en noticias_bert_clean.
    """
    # Verificar que el usuario tenga un plan que permita acceso
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Se requiere autenticación para acceder a las noticias con IA"
        )
    
    user_plan = (current_user.get("plan") or "free").lower()
    user_role = (current_user.get("rol") or "user").lower()
    
    # Admin tiene acceso a todo, enterprise y premium también tienen acceso
    if user_role == "admin":
        # Admin tiene acceso completo, continuar sin restricciones
        pass
    elif user_plan not in ["enterprise", "premium"]:
        raise HTTPException(
            status_code=403,
            detail="Esta funcionalidad solo está disponible para usuarios con plan Enterprise o Premium. Por favor, actualiza tu plan para acceder."
        )
    conn = get_conn()
    if not conn:
        raise HTTPException(status_code=500, detail="Error conectando a la base de datos")
    
    cursor = None
    try:
        cursor = conn.cursor()
        
        select_query = """
            SELECT 
                nbc.id as bert_clean_id,
                nl.id as noticia_id,
                COALESCE(nl.titulo, nbc.titulo) as titulo,
                nl.resumen,
                nl.contenido as contenido_original,
                nl.categoria,
                nl.autor,
                nl.keywords,
                COALESCE(nl.url, nbc.url) as url,
                nl.dominio,
                COALESCE(nl.fecha, nbc.fecha)::text as fecha,
                nl.hora::text as hora,
                COALESCE(nl.fuente, nbc.fuente) as fuente,
                nl.imagen_principal,
                nl.cantidad_imagenes,
                nl.tiene_imagenes,
                nbc.contenido_limpio,
                nbc.parrafos_relevantes,
                nbc.parrafos_irrelevantes,
                nbc.num_parrafos_total,
                nbc.num_parrafos_relevantes,
                nbc.num_parrafos_irrelevantes,
                nbc.modelo_usado,
                nbc.procesado_at::text as procesado_at,
                CASE 
                    WHEN nbc.num_parrafos_total > 0 AND nbc.num_parrafos_total IS NOT NULL
                    THEN ROUND((COALESCE(nbc.num_parrafos_relevantes, 0)::numeric / nbc.num_parrafos_total::numeric) * 100, 2)
                    ELSE 0
                END as porcentaje_relevancia
            FROM noticias_bert_clean nbc
            INNER JOIN noticias_limpia nl ON nbc.noticia_id = nl.id
            WHERE nl.id = %s
            LIMIT 1
        """
        
        cursor.execute(select_query, (noticia_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Noticia con IA no encontrada")
        
        # Parsear JSON de párrafos
        parrafos_relevantes = None
        parrafos_irrelevantes = None
        
        if row[17]:  # parrafos_relevantes
            try:
                if isinstance(row[17], str):
                    parrafos_relevantes = json.loads(row[17])
                else:
                    parrafos_relevantes = row[17]
            except:
                parrafos_relevantes = []
        
        if row[18]:  # parrafos_irrelevantes
            try:
                if isinstance(row[18], str):
                    parrafos_irrelevantes = json.loads(row[18])
                else:
                    parrafos_irrelevantes = row[18]
            except:
                parrafos_irrelevantes = []
        
        return NewsIA(
            bert_clean_id=row[0],
            noticia_id=row[1],
            titulo=row[2] or "",
            resumen=row[3],
            contenido_original=row[4],
            categoria=row[5],
            autor=row[6],
            keywords=row[7],
            url=row[8],
            dominio=row[9],
            fecha=row[10],
            hora=row[11],
            fuente=row[12],
            imagen_principal=row[13],
            cantidad_imagenes=row[14],
            tiene_imagenes=row[15],
            contenido_limpio=row[16],
            parrafos_relevantes=parrafos_relevantes,
            parrafos_irrelevantes=parrafos_irrelevantes,
            num_parrafos_total=row[19],
            num_parrafos_relevantes=row[20],
            num_parrafos_irrelevantes=row[21],
            modelo_usado=row[22],
            procesado_at=row[23],
            porcentaje_relevancia=float(row[24]) if row[24] else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo noticia IA pública: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo noticia: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        put_conn(conn)

