from datetime import datetime, time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class News(BaseModel):
    id: int
    titulo: Optional[str] = None
    fecha: Optional[datetime] = None
    hora: Optional[time] = None
    anio: Optional[float] = None
    mes: Optional[float] = None
    dia: Optional[float] = None
    dia_semana: Optional[str] = None
    resumen: Optional[str] = None
    contenido: Optional[str] = None
    categoria: Optional[str] = None
    autor: Optional[str] = None
    keywords: Optional[str] = None
    url: Optional[str] = None
    dominio: Optional[str] = None
    fecha_extraccion: Optional[datetime] = None
    imagen_principal: Optional[str] = None
    cantidad_imagenes: Optional[int] = None
    tiene_imagenes: Optional[bool] = None
    fuente: Optional[str] = None
    longitud_titulo: Optional[int] = None
    longitud_resumen: Optional[float] = None
    tipo_contenido: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Campos legacy para compatibilidad
    tags: Optional[str] = None
    imagenes: Optional[str] = None


class NewsListResponse(BaseModel):
    total: int
    items: list[News]


class NewsFilters(BaseModel):
    """Filtros avanzados para noticias"""
    q: Optional[str] = None  # Búsqueda de texto
    categoria: Optional[str] = None
    fuente: Optional[str] = None
    dominio: Optional[str] = None
    anio: Optional[int] = None
    mes: Optional[int] = None
    dia: Optional[int] = None
    dia_semana: Optional[str] = None
    tipo_contenido: Optional[str] = None
    tiene_imagenes: Optional[bool] = None
    longitud_titulo_min: Optional[int] = None
    longitud_titulo_max: Optional[int] = None
    longitud_resumen_min: Optional[float] = None
    longitud_resumen_max: Optional[float] = None
    fecha_desde: Optional[str] = None
    fecha_hasta: Optional[str] = None
    keywords: Optional[str] = None  # Búsqueda en keywords


class NewsStats(BaseModel):
    """Estadísticas de noticias"""
    total_noticias: int
    noticias_por_fuente: Dict[str, int]
    noticias_por_categoria: Dict[str, int]
    noticias_por_mes: Dict[str, int]
    noticias_por_dia_semana: Dict[str, int]
    noticias_por_tipo_contenido: Dict[str, int]
    noticias_con_imagenes: int
    noticias_sin_imagenes: int
    promedio_longitud_titulo: float
    promedio_longitud_resumen: float
    dominios_unicos: int
    rango_fechas: Dict[str, str]  # fecha_min, fecha_max


class NewsSearchResponse(BaseModel):
    """Respuesta de búsqueda avanzada"""
    total: int
    items: List[News]
    filtros_aplicados: NewsFilters
    estadisticas: Optional[NewsStats] = None


class NewsMetrics(BaseModel):
    """Métricas detalladas de noticias"""
    total: int
    con_imagenes: int
    sin_imagenes: int
    promedio_titulo: float
    promedio_resumen: float
    fuentes_activas: int
    categorias_activas: int
    dominios_unicos: int

