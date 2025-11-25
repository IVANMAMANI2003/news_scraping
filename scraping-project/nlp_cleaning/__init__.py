"""
Módulo de Limpieza Avanzada de Noticias usando Ollama

Este módulo implementa un sistema de selección de contenido relevante
usando Ollama (deepseek-r1:8b) para limpiar contenido de noticias extraído por scraping.

Autor: Sistema de Limpieza NLP
Fecha: 2024
"""

from .nlp_cleaner import NLPContentCleaner, clean_news, get_cleaner_instance

__all__ = [
    'clean_news',
    'NLPContentCleaner',
    'get_cleaner_instance'
]

__version__ = '2.0.0'
