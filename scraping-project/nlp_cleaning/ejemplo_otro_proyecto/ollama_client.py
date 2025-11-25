"""
Cliente para Ollama
===================

Este módulo proporciona un cliente para comunicarse con Ollama
y generar respuestas usando modelos locales.

Modelo por defecto: deepseek-r1
"""

import json
import warnings
from typing import Any, Dict, Optional

import requests

warnings.filterwarnings('ignore')


class OllamaClient:
    """
    Cliente para interactuar con Ollama API.
    
    Atributos:
        base_url (str): URL base de Ollama API.
        model (str): Nombre del modelo a utilizar.
        timeout (int): Timeout para las peticiones en segundos.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", 
                 model: str = "deepseek-r1:8b", timeout: int = 120):
        """
        Inicializa el cliente de Ollama.
        
        Args:
            base_url (str): URL base de Ollama API. Por defecto "http://localhost:11434".
            model (str): Nombre del modelo a utilizar. Por defecto "deepseek-r1".
            timeout (int): Timeout para las peticiones en segundos. Por defecto 120.
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        
        # Verificar conexión con Ollama
        self._check_connection()
    
    def _check_connection(self):
        """
        Verifica la conexión con Ollama.
        
        Raises:
            ConnectionError: Si no se puede conectar a Ollama.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"✅ Conectado a Ollama en {self.base_url}")
                # Verificar que el modelo esté disponible
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                if self.model not in model_names:
                    print(f"⚠️  Advertencia: Modelo '{self.model}' no encontrado en Ollama")
                    print(f"   Modelos disponibles: {', '.join(model_names[:5])}")
            else:
                raise ConnectionError(f"Ollama respondió con código {response.status_code}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"No se pudo conectar a Ollama en {self.base_url}. "
                f"Asegúrate de que Ollama esté ejecutándose."
            )
        except Exception as e:
            raise ConnectionError(f"Error al verificar conexión con Ollama: {e}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 stream: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Genera una respuesta usando Ollama.
        
        Args:
            prompt (str): Prompt para el modelo.
            system_prompt (str, optional): Prompt del sistema (instrucciones del modelo).
            stream (bool): Si es True, retorna un generador. Por defecto False.
            **kwargs: Argumentos adicionales para la API de Ollama.
        
        Returns:
            dict: Respuesta del modelo con:
                - response: Texto generado
                - model: Nombre del modelo usado
                - done: Si la generación está completa
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            **kwargs
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            print(f"🔄 Generando respuesta con Ollama (modelo: {self.model})...")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            
            response.raise_for_status()
            
            if stream:
                # Retornar generador para streaming
                return self._handle_stream_response(response)
            else:
                # Respuesta completa
                result = response.json()
                generated_text = result.get('response', '')
                
                print(f"✅ Respuesta generada: {len(generated_text)} caracteres")
                
                return {
                    'response': generated_text.strip(),
                    'model': result.get('model', self.model),
                    'done': result.get('done', True),
                    'context': result.get('context', []),
                    'total_duration': result.get('total_duration', 0),
                    'load_duration': result.get('load_duration', 0),
                    'prompt_eval_count': result.get('prompt_eval_count', 0),
                    'prompt_eval_duration': result.get('prompt_eval_duration', 0),
                    'eval_count': result.get('eval_count', 0),
                    'eval_duration': result.get('eval_duration', 0)
                }
                
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Timeout al generar respuesta (>{self.timeout}s)")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error al comunicarse con Ollama: {e}")
    
    def _handle_stream_response(self, response):
        """
        Maneja respuestas en streaming de Ollama.
        
        Args:
            response: Objeto de respuesta de requests.
        
        Yields:
            dict: Chunks de la respuesta.
        """
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    yield chunk
                except json.JSONDecodeError:
                    continue
    
    def chat(self, messages: list, stream: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Realiza una conversación con el modelo usando formato de chat.
        
        Args:
            messages (list): Lista de mensajes en formato:
                [{"role": "user", "content": "..."}, ...]
            stream (bool): Si es True, retorna un generador. Por defecto False.
            **kwargs: Argumentos adicionales para la API de Ollama.
        
        Returns:
            dict: Respuesta del modelo.
        """
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        try:
            print(f"🔄 Enviando mensaje a Ollama (modelo: {self.model})...")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                stream=stream
            )
            
            response.raise_for_status()
            
            if stream:
                return self._handle_stream_response(response)
            else:
                result = response.json()
                message = result.get('message', {})
                
                print(f"✅ Respuesta recibida: {len(message.get('content', ''))} caracteres")
                
                return {
                    'response': message.get('content', '').strip(),
                    'model': result.get('model', self.model),
                    'done': result.get('done', True),
                    'message': message
                }
                
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Timeout al chatear (>{self.timeout}s)")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error al comunicarse con Ollama: {e}")
    
    def generate_adaptive_question(self, user_text: str, user_emotion: str,
                                 context: Optional[str] = None,
                                 text_sentiment: Optional[str] = None,
                                 text_emotion: Optional[str] = None,
                                 text_polarity: Optional[float] = None,
                                 valence: Optional[float] = None,
                                 arousal: Optional[float] = None,
                                 dominance: Optional[float] = None) -> str:
        """
        Genera una pregunta adaptativa basada en el texto, emoción de voz y análisis de texto.
        
        Args:
            user_text (str): Texto transcrito del usuario.
            user_emotion (str): Emoción detectada en el tono de voz (happy, sad, angry, neutral, etc.).
            context (str, optional): Contexto adicional de la conversación.
            text_sentiment (str, optional): Sentimiento del texto (positive, negative, neutral).
            text_emotion (str, optional): Emoción detectada en el contenido del texto.
            text_polarity (float, optional): Polaridad del texto (-1.0 a 1.0).
            valence (float, optional): Dimensión de valence (-1.0 a 1.0, positivo=feliz, negativo=triste).
            arousal (float, optional): Dimensión de arousal (-1.0 a 1.0, alto=excitado, bajo=calmado).
            dominance (float, optional): Dimensión de dominance (-1.0 a 1.0, alto=confiado, bajo=sumiso).
        
        Returns:
            str: Pregunta adaptativa generada.
        """
        # Mapeo de emociones a descripciones en español
        emotion_descriptions = {
            'happy': 'alegre y positivo',
            'sad': 'triste y melancólico',
            'angry': 'enojado y frustrado',
            'neutral': 'neutral y calmado',
            'fear': 'temeroso y ansioso',
            'surprise': 'sorprendido y asombrado',
            'disgust': 'disgustado y desagradado'
        }
        
        # Mapeo de sentimientos
        sentiment_descriptions = {
            'positive': 'positivo',
            'negative': 'negativo',
            'neutral': 'neutro'
        }
        
        emotion_desc = emotion_descriptions.get(user_emotion.lower(), user_emotion)
        sentiment_desc = sentiment_descriptions.get(text_sentiment.lower() if text_sentiment else '', 'neutro')
        
        # Construir prompt
        system_prompt = (
            "Eres un asistente empático que conversa con un usuario. "
            "Tu objetivo es hacer preguntas que demuestren comprensión y empatía, "
            "adaptándote al estado emocional del usuario tanto en su tono de voz como en el contenido de sus palabras. "
            "Las preguntas deben ser naturales, coherentes y mostrar interés genuino."
        )
        
        prompt = (
            f"El usuario acaba de decir: \"{user_text}\"\n\n"
            f"Análisis emocional:\n"
            f"- Emoción detectada en el tono de voz: {emotion_desc} ({user_emotion})\n"
        )
        
        # Agregar dimensiones del modelo avanzado si están disponibles
        if valence is not None and arousal is not None and dominance is not None:
            valence_desc = "muy positivo" if valence > 0.7 else "positivo" if valence > 0.3 else "neutro" if valence > -0.3 else "negativo" if valence > -0.7 else "muy negativo"
            arousal_desc = "muy excitado" if arousal > 0.7 else "excitado" if arousal > 0.3 else "calmado" if arousal > -0.3 else "muy calmado" if arousal > -0.7 else "apático"
            dominance_desc = "muy confiado" if dominance > 0.7 else "confiado" if dominance > 0.3 else "neutral" if dominance > -0.3 else "sumiso" if dominance > -0.7 else "muy sumiso"
            
            prompt += f"- Dimensiones emocionales (modelo avanzado):\n"
            prompt += f"  * Valence: {valence_desc} ({valence:.2f}) - Positivo=feliz, Negativo=triste\n"
            prompt += f"  * Arousal: {arousal_desc} ({arousal:.2f}) - Alto=excitado, Bajo=calmado\n"
            prompt += f"  * Dominance: {dominance_desc} ({dominance:.2f}) - Alto=confiado, Bajo=sumiso\n"
        
        # Agregar análisis de texto si está disponible
        if text_sentiment:
            prompt += f"- Sentimiento del contenido del texto: {sentiment_desc} ({text_sentiment})\n"
        
        if text_emotion:
            text_emotion_desc = emotion_descriptions.get(text_emotion.lower(), text_emotion)
            prompt += f"- Emoción detectada en el contenido del texto: {text_emotion_desc} ({text_emotion})\n"
        
        if text_polarity is not None:
            polarity_desc = "muy positivo" if text_polarity > 0.5 else "positivo" if text_polarity > 0 else "negativo" if text_polarity < -0.5 else "muy negativo" if text_polarity < 0 else "neutro"
            prompt += f"- Polaridad del texto: {polarity_desc} ({text_polarity:.2f})\n"
        
        prompt += "\n"
        
        # Si hay discrepancia entre tono de voz y contenido del texto, mencionarlo
        if text_emotion and user_emotion != text_emotion:
            prompt += (
                f"Nota importante: Hay una discrepancia entre el tono de voz ({user_emotion}) "
                f"y el contenido del texto ({text_emotion}). "
                f"Considera ambos aspectos al generar la pregunta.\n\n"
            )
        
        if context:
            prompt += f"Contexto de la conversación: {context}\n\n"
        
        prompt += (
            "Genera una pregunta empática y coherente basada en toda esta información. "
            "La pregunta debe ser breve (1-2 oraciones máximo), "
            "mostrar comprensión de su estado emocional (tanto en voz como en palabras) "
            "y invitar a continuar la conversación."
        )
        
        try:
            result = self.generate(prompt, system_prompt=system_prompt)
            return result['response']
        except Exception as e:
            raise RuntimeError(f"Error al generar pregunta adaptativa: {e}")
