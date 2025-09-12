from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel


class News(BaseModel):
    id: int
    titulo: Optional[str] = None
    fecha: Optional[datetime] = None
    hora: Optional[time] = None
    resumen: Optional[str] = None
    contenido: Optional[str] = None
    categoria: Optional[str] = None
    autor: Optional[str] = None
    tags: Optional[str] = None
    url: Optional[str] = None
    fecha_extraccion: Optional[datetime] = None
    imagenes: Optional[str] = None
    fuente: Optional[str] = None
    created_at: Optional[datetime] = None


class NewsListResponse(BaseModel):
    total: int
    items: list[News]

