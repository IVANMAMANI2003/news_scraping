"""
Módulo Bot Dinámico con IA
==========================

Este módulo proporciona un bot conversacional que:
- Captura respuestas del usuario desde el micrófono
- Analiza voz usando voice_ai_module (STT + SER)
- Genera preguntas adaptativas usando Ollama (deepseek-r1)
- Mantiene conversaciones empáticas basadas en emociones

Componentes principales:
- bot: Bot conversacional principal
- ollama_client: Cliente para comunicación con Ollama
"""

from .bot import DynamicBot
from .conversation_storage import ConversationStorage
from .ollama_client import OllamaClient

__all__ = [
    'DynamicBot',
    'OllamaClient',
    'ConversationStorage'
]

__version__ = '1.0.0'
