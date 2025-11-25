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


# ============================================
# Modelos de Autenticación y Usuarios
# ============================================

class UserBase(BaseModel):
    email: str
    nombre: str
    apellido: Optional[str] = None


class UserCreate(UserBase):
    password: str
    plan: Optional[str] = "free"


class UserUpdate(BaseModel):
    email: Optional[str] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    activo: Optional[bool] = None
    rol: Optional[str] = None
    plan: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    id: int
    activo: bool
    rol: str
    plan: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    email_verificado: bool

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    total: int
    items: List[User]


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User
    expires_in: int = 3600


class TokenData(BaseModel):
    user_id: int
    email: str
    rol: str


class APIKeyBase(BaseModel):
    nombre: str
    plan: str = "free"


class APIKeyCreate(APIKeyBase):
    usuario_id: int
    limite_diario: Optional[int] = None
    fuente_permitida: Optional[str] = None
    max_sources: Optional[int] = None
    keywords: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    historial_dias: Optional[int] = None
    expires_at: Optional[datetime] = None


class APIKeyUpdate(BaseModel):
    nombre: Optional[str] = None
    plan: Optional[str] = None
    activo: Optional[bool] = None
    limite_diario: Optional[int] = None
    fuente_permitida: Optional[str] = None
    max_sources: Optional[int] = None
    keywords: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    historial_dias: Optional[int] = None
    expires_at: Optional[datetime] = None


class APIKey(APIKeyBase):
    id: int
    usuario_id: int
    key: str
    activo: bool
    requests_today: int
    requests_total: int
    last_reset: Optional[datetime] = None
    last_used: Optional[datetime] = None
    fuente_permitida: Optional[str] = None
    max_sources: int
    keywords: Optional[List[str]] = None
    webhook_url: Optional[str] = None
    historial_dias: int
    limite_diario: int
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    total: int
    items: List[APIKey]


class APIKeyStats(BaseModel):
    requests_today: int
    requests_total: int
    limite_diario: int
    porcentaje_uso: float
    last_used: Optional[datetime] = None

