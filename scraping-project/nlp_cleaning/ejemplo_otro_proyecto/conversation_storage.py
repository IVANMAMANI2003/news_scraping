"""
Servicio para guardar conversaciones en el backend
==================================================

Este módulo proporciona funcionalidades para guardar las conversaciones
del bot en la base de datos a través del backend Spring Boot.
"""

import json
import warnings
from typing import Any, Dict, List, Optional

import requests

warnings.filterwarnings('ignore')


class ConversationStorage:
    """
    Cliente para guardar conversaciones en el backend.
    
    Atributos:
        backend_url (str): URL base del backend Spring Boot.
        timeout (int): Timeout para las peticiones en segundos.
    """
    
    def __init__(self, backend_url: str = "http://localhost:8080/api", timeout: int = 30):
        """
        Inicializa el cliente de almacenamiento.
        
        Args:
            backend_url (str): URL base del backend. Por defecto "http://localhost:8080/api".
            timeout (int): Timeout para las peticiones. Por defecto 30.
        """
        self.backend_url = backend_url.rstrip('/')
        self.timeout = timeout
        self.conversations_endpoint = f"{self.backend_url}/conversations"
    
    def save_conversation(self, conversation_data: Dict[str, Any]) -> Optional[str]:
        """
        Guarda una conversación completa en el backend.
        
        Args:
            conversation_data (dict): Datos de la conversación con estructura:
                {
                    "studentId": "uuid" (opcional),
                    "totalTurns": int,
                    "summary": str (opcional),
                    "turns": [
                        {
                            "turnNumber": int,
                            "userText": str,
                            "userEmotion": str,
                            "emotionConfidence": float,
                            "allEmotionScores": dict,
                            "combinedEmotion": str,
                            "botQuestion": str,
                            "ollamaModel": str
                        },
                        ...
                    ]
                }
        
        Returns:
            str: ID de la conversación guardada, o None si hubo error.
        """
        try:
            print(f"💾 Guardando conversación en el backend...")
            
            # Preparar datos para el backend
            payload = {
                "studentId": conversation_data.get("studentId"),
                "totalTurns": conversation_data.get("totalTurns", 0),
                "summary": conversation_data.get("summary"),
                "turns": []
            }
            
            # Convertir turnos
            for turn in conversation_data.get("turns", []):
                turn_payload = {
                    "turnNumber": turn.get("turnNumber"),
                    "userText": turn.get("userText", ""),
                    "userEmotion": turn.get("userEmotion", "neutral"),
                    "emotionConfidence": float(turn.get("emotionConfidence", 0.0)),
                    "allEmotionScores": turn.get("allEmotionScores", {}),
                    "combinedEmotion": turn.get("combinedEmotion", ""),
                    # Análisis de texto
                    "textSentiment": turn.get("textSentiment"),
                    "textSentimentScore": float(turn.get("textSentimentScore", 0.0)) if turn.get("textSentimentScore") is not None else None,
                    "textEmotion": turn.get("textEmotion"),
                    "textEmotionScore": float(turn.get("textEmotionScore", 0.0)) if turn.get("textEmotionScore") is not None else None,
                    "textPolarity": float(turn.get("textPolarity", 0.0)) if turn.get("textPolarity") is not None else None,
                    "allTextSentimentScores": turn.get("allTextSentimentScores", {}),
                    "botQuestion": turn.get("botQuestion", ""),
                    "ollamaModel": turn.get("ollamaModel", "deepseek-r1:8b")
                }
                payload["turns"].append(turn_payload)
            
            # Enviar al backend
            response = requests.post(
                f"{self.conversations_endpoint}/complete",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            
            result = response.json()
            conversation_id = result.get("id")
            
            print(f"✅ Conversación guardada exitosamente (ID: {conversation_id})")
            return conversation_id
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Error: No se pudo conectar al backend en {self.backend_url}")
            print("   Verifica que el backend Spring Boot esté ejecutándose")
            return None
        except requests.exceptions.Timeout:
            print(f"❌ Error: Timeout al guardar conversación (>{self.timeout}s)")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al guardar conversación: {e}")
            if hasattr(e.response, 'text'):
                print(f"   Respuesta del servidor: {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return None
    
    def save_turn(self, conversation_id: str, turn_data: Dict[str, Any]) -> bool:
        """
        Agrega un turno a una conversación existente.
        
        Args:
            conversation_id (str): ID de la conversación.
            turn_data (dict): Datos del turno.
        
        Returns:
            bool: True si se guardó exitosamente, False en caso contrario.
        """
        try:
            payload = {
                "turnNumber": turn_data.get("turnNumber"),
                "userText": turn_data.get("userText", ""),
                "userEmotion": turn_data.get("userEmotion", "neutral"),
                "emotionConfidence": float(turn_data.get("emotionConfidence", 0.0)),
                "allEmotionScores": turn_data.get("allEmotionScores", {}),
                "combinedEmotion": turn_data.get("combinedEmotion", ""),
                # Análisis de texto
                "textSentiment": turn_data.get("textSentiment"),
                "textSentimentScore": float(turn_data.get("textSentimentScore", 0.0)) if turn_data.get("textSentimentScore") is not None else None,
                "textEmotion": turn_data.get("textEmotion"),
                "textEmotionScore": float(turn_data.get("textEmotionScore", 0.0)) if turn_data.get("textEmotionScore") is not None else None,
                "textPolarity": float(turn_data.get("textPolarity", 0.0)) if turn_data.get("textPolarity") is not None else None,
                "allTextSentimentScores": turn_data.get("allTextSentimentScores", {}),
                "botQuestion": turn_data.get("botQuestion", ""),
                "ollamaModel": turn_data.get("ollamaModel", "deepseek-r1:8b")
            }
            
            response = requests.post(
                f"{self.conversations_endpoint}/{conversation_id}/turns",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            print(f"✅ Turno guardado exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar turno: {e}")
            return False
    
    def get_conversations(self, student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene conversaciones del backend.
        
        Args:
            student_id (str, optional): ID del estudiante para filtrar.
        
        Returns:
            list: Lista de conversaciones.
        """
        try:
            if student_id:
                url = f"{self.conversations_endpoint}/student/{student_id}"
            else:
                url = self.conversations_endpoint
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Error al obtener conversaciones: {e}")
            return []
