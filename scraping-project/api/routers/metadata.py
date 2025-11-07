from typing import List

from fastapi import APIRouter

from ..db import get_conn, put_conn

router = APIRouter()


@router.get("/dominios/listar", response_model=List[str])
def list_dominios():
    """Obtiene la lista de todos los dominios disponibles"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT dominio FROM noticias_limpia 
            WHERE dominio IS NOT NULL AND dominio != ''
            ORDER BY dominio
            """
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]
    finally:
        put_conn(conn)


@router.get("/tipos-contenido/listar", response_model=List[str])
def list_tipos_contenido():
    """Obtiene la lista de todos los tipos de contenido disponibles"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT tipo_contenido FROM noticias_limpia 
            WHERE tipo_contenido IS NOT NULL AND tipo_contenido != ''
            ORDER BY tipo_contenido
            """
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]
    finally:
        put_conn(conn)


@router.get("/dias-semana/listar", response_model=List[str])
def list_dias_semana():
    """Obtiene la lista de todos los días de la semana disponibles"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT dia_semana FROM noticias_limpia 
            WHERE dia_semana IS NOT NULL AND dia_semana != ''
            ORDER BY dia_semana
            """
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]
    finally:
        put_conn(conn)


@router.get("/anos/listar", response_model=List[int])
def list_anos():
    """Obtiene la lista de todos los años disponibles"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT anio FROM noticias_limpia 
            WHERE anio IS NOT NULL
            ORDER BY anio DESC
            """
        )
        rows = cur.fetchall()
        return [int(row[0]) for row in rows]
    finally:
        put_conn(conn)


@router.get("/meses/listar", response_model=List[int])
def list_meses():
    """Obtiene la lista de todos los meses disponibles"""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT mes FROM noticias_limpia 
            WHERE mes IS NOT NULL
            ORDER BY mes
            """
        )
        rows = cur.fetchall()
        return [int(row[0]) for row in rows]
    finally:
        put_conn(conn)
