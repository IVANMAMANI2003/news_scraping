"""
Bot Dinámico con IA
===================

Este módulo proporciona un bot conversacional que:
- Captura respuestas del usuario desde el micrófono
- Analiza voz usando voice_ai_module (STT + SER)
- Genera preguntas adaptativas usando Ollama
"""

import os
import sys
from typing import Any, Dict, List, Optional

# Agregar el directorio raíz al path para importar voice_ai_module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.voice_ai_module import AudioRecorder, VoiceAIFusion

from .conversation_storage import ConversationStorage
from .ollama_client import OllamaClient


class DynamicBot:
    """
    Bot conversacional dinámico que integra análisis de voz con generación de preguntas.
    
    Atributos:
        voice_fusion: Fusionador de voz (STT + SER).
        ollama_client: Cliente de Ollama.
        recorder: Grabador de audio.
        conversation_history: Historial de la conversación.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434",
                 ollama_model: str = "deepseek-r1:8b",  # Usar versión 8b por defecto
                 backend_url: str = "http://localhost:8080/api",
                 sample_rate: int = 16000,
                 record_duration: float = 5.0,
                 save_to_database: bool = True):
        """
        Inicializa el bot dinámico.
        
        Args:
            ollama_url (str): URL de Ollama API. Por defecto "http://localhost:11434".
            ollama_model (str): Modelo de Ollama a utilizar. Por defecto "deepseek-r1:8b".
            backend_url (str): URL del backend Spring Boot. Por defecto "http://localhost:8080/api".
            sample_rate (int): Tasa de muestreo del audio. Por defecto 16000.
            record_duration (float): Duración de grabación por defecto en segundos. Por defecto 5.0.
            save_to_database (bool): Si guardar conversaciones en la base de datos. Por defecto True.
        """
        print("🤖 Inicializando Bot Dinámico...")
        print()
        
        # Inicializar componentes de voz
        print("📋 Paso 1: Inicializando módulo de voz...")
        self.recorder = AudioRecorder(sample_rate=sample_rate, channels=1)
        self.voice_fusion = VoiceAIFusion()
        self.record_duration = record_duration
        print("✅ Módulo de voz inicializado")
        print()
        
        # Inicializar cliente de Ollama
        print("📋 Paso 2: Inicializando cliente de Ollama...")
        self.ollama_client = OllamaClient(base_url=ollama_url, model=ollama_model)
        print("✅ Cliente de Ollama inicializado")
        print()
        
        # Inicializar almacenamiento de conversaciones
        self.save_to_database = save_to_database
        if save_to_database:
            print("📋 Paso 3: Inicializando almacenamiento de conversaciones...")
            self.storage = ConversationStorage(backend_url=backend_url)
            print("✅ Almacenamiento inicializado")
            print()
        
        # Historial de conversación
        self.conversation_history: List[Dict[str, Any]] = []
        self.current_conversation_id: Optional[str] = None
        
        print("✅ Bot Dinámico inicializado correctamente")
        print()
    
    def capture_and_analyze(self, duration: Optional[float] = None) -> Dict[str, Any]:
        """
        Captura audio del usuario y lo analiza (STT + SER).
        
        Args:
            duration (float, optional): Duración de la grabación en segundos.
                                      Si es None, usa record_duration por defecto.
        
        Returns:
            dict: Resultados del análisis:
                - transcription: Texto transcrito
                - voice_emotion_tone: Emoción detectada
                - tone_score: Score de confianza
                - all_tone_scores: Todas las emociones y scores
                - combined_emotion: Análisis combinado
        """
        if duration is None:
            duration = self.record_duration
        
        print(f"🎙️  Grabando audio del usuario ({duration} segundos)...")
        print("   Habla ahora...")
        print()
        
        # Grabar audio
        audio_data = self.recorder.record(duration)
        
        # Analizar audio (STT + SER)
        print("🔄 Analizando audio (STT + SER)...")
        result = self.voice_fusion.process(audio_data, sample_rate=self.recorder.sample_rate, language='es')
        
        print()
        print("📊 Resultados del análisis:")
        print(f"   Texto: \"{result['transcription']}\"")
        print(f"   Emoción: {result['voice_emotion_tone']} (confianza: {result['tone_score']:.1%})")
        print()
        
        return result
    
    def generate_question(self, user_text: str, user_emotion: str,
                         context: Optional[str] = None,
                         text_sentiment: Optional[str] = None,
                         text_emotion: Optional[str] = None,
                         text_polarity: Optional[float] = None,
                         valence: Optional[float] = None,
                         arousal: Optional[float] = None,
                         dominance: Optional[float] = None) -> str:
        """
        Genera una pregunta adaptativa usando Ollama.
        
        Args:
            user_text (str): Texto transcrito del usuario.
            user_emotion (str): Emoción detectada en el tono de voz.
            context (str, optional): Contexto adicional.
            text_sentiment (str, optional): Sentimiento del texto.
            text_emotion (str, optional): Emoción detectada en el texto.
            text_polarity (float, optional): Polaridad del texto.
            valence (float, optional): Dimensión de valence del modelo avanzado.
            arousal (float, optional): Dimensión de arousal del modelo avanzado.
            dominance (float, optional): Dimensión de dominance del modelo avanzado.
        
        Returns:
            str: Pregunta adaptativa generada.
        """
        print("🤖 Generando pregunta adaptativa con Ollama...")
        print()
        
        try:
            question = self.ollama_client.generate_adaptive_question(
                user_text=user_text,
                user_emotion=user_emotion,
                context=context,
                text_sentiment=text_sentiment,
                text_emotion=text_emotion,
                text_polarity=text_polarity,
                valence=valence,
                arousal=arousal,
                dominance=dominance
            )
            
            print(f"✅ Pregunta generada: \"{question}\"")
            print()
            
            return question
            
        except Exception as e:
            print(f"❌ Error al generar pregunta: {e}")
            print()
            # Pregunta de respaldo
            return "¿Podrías contarme más sobre eso?"
    
    def converse(self, num_turns: int = 3, duration: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Realiza una conversación completa con el usuario.
        
        Args:
            num_turns (int): Número de turnos de conversación. Por defecto 3.
            duration (float, optional): Duración de cada grabación. Si es None, usa record_duration.
        
        Returns:
            list: Historial completo de la conversación.
        """
        print("=" * 60)
        print("💬 INICIANDO CONVERSACIÓN")
        print("=" * 60)
        print()
        
        conversation = []
        
        for turn in range(1, num_turns + 1):
            print(f"🔄 Turno {turn}/{num_turns}")
            print("-" * 60)
            print()
            
            # Capturar y analizar respuesta del usuario
            analysis = self.capture_and_analyze(duration=duration)
            
            user_text = analysis['transcription']
            user_emotion = analysis['voice_emotion_tone']
            
            # Construir contexto de la conversación
            context = None
            if conversation:
                context = "Conversación previa:\n"
                for i, msg in enumerate(conversation[-2:], 1):  # Últimos 2 mensajes
                    context += f"{i}. Usuario: {msg.get('user_text', '')} "
                    context += f"(Emoción: {msg.get('user_emotion', '')})\n"
                    context += f"   Bot: {msg.get('bot_question', '')}\n"
            
            # Generar pregunta adaptativa con análisis de texto y dimensiones
            bot_question = self.generate_question(
                user_text=user_text,
                user_emotion=user_emotion,
                context=context,
                text_sentiment=analysis.get('text_sentiment'),
                text_emotion=analysis.get('text_emotion'),
                text_polarity=analysis.get('text_polarity'),
                valence=analysis.get('valence'),
                arousal=analysis.get('arousal'),
                dominance=analysis.get('dominance')
            )
            
            # Guardar en historial
            turn_data = {
                'turn': turn,
                'user_text': user_text,
                'user_emotion': user_emotion,
                'tone_score': analysis['tone_score'],
                'bot_question': bot_question,
                'analysis': analysis,
                'all_emotion_scores': analysis.get('all_tone_scores', {}),
                'combined_emotion': analysis.get('combined_emotion', ''),
                'ollama_model': self.ollama_client.model
            }
            
            conversation.append(turn_data)
            self.conversation_history.append(turn_data)
            
            # Guardar turno en base de datos si está habilitado
            if self.save_to_database and self.current_conversation_id:
                self.storage.save_turn(self.current_conversation_id, {
                    'turnNumber': turn,
                    'userText': user_text,
                    'userEmotion': user_emotion,
                    'emotionConfidence': analysis['tone_score'],
                    'allEmotionScores': analysis.get('all_tone_scores', {}),
                    'combinedEmotion': analysis.get('combined_emotion', ''),
                    # Análisis de texto
                    'textSentiment': analysis.get('text_sentiment'),
                    'textSentimentScore': analysis.get('text_sentiment_score'),
                    'textEmotion': analysis.get('text_emotion'),
                    'textEmotionScore': analysis.get('text_emotion_score'),
                    'textPolarity': analysis.get('text_polarity'),
                    'allTextSentimentScores': analysis.get('all_text_sentiment_scores', {}),
                    'botQuestion': bot_question,
                    'ollamaModel': self.ollama_client.model
                })
            
            # Mostrar pregunta del bot
            print("🤖 Bot:")
            print(f"   {bot_question}")
            print()
            
            # Si no es el último turno, esperar respuesta
            if turn < num_turns:
                print("   (Presiona Enter para continuar al siguiente turno...)")
                input()
                print()
        
        # Guardar conversación completa en base de datos
        if self.save_to_database:
            print("💾 Guardando conversación completa en la base de datos...")
            conversation_data = {
                'totalTurns': num_turns,
                'summary': self.get_conversation_summary(),
                'turns': [
                    {
                        'turnNumber': turn_data['turn'],
                        'userText': turn_data['user_text'],
                        'userEmotion': turn_data['user_emotion'],
                        'emotionConfidence': turn_data['tone_score'],
                        'allEmotionScores': turn_data.get('all_emotion_scores', {}),
                        'combinedEmotion': turn_data.get('combined_emotion', ''),
                        # Análisis de texto
                        'textSentiment': turn_data.get('analysis', {}).get('text_sentiment'),
                        'textSentimentScore': turn_data.get('analysis', {}).get('text_sentiment_score'),
                        'textEmotion': turn_data.get('analysis', {}).get('text_emotion'),
                        'textEmotionScore': turn_data.get('analysis', {}).get('text_emotion_score'),
                        'textPolarity': turn_data.get('analysis', {}).get('text_polarity'),
                        'allTextSentimentScores': turn_data.get('analysis', {}).get('all_text_sentiment_scores', {}),
                        'botQuestion': turn_data['bot_question'],
                        'ollamaModel': turn_data.get('ollama_model', self.ollama_client.model)
                    }
                    for turn_data in conversation
                ]
            }
            
            conversation_id = self.storage.save_conversation(conversation_data)
            if conversation_id:
                self.current_conversation_id = conversation_id
                print(f"✅ Conversación guardada con ID: {conversation_id}")
            print()
        
        print("=" * 60)
        print("✅ CONVERSACIÓN COMPLETADA")
        print("=" * 60)
        print()
        
        return conversation
    
    def get_conversation_summary(self) -> str:
        """
        Obtiene un resumen de la conversación.
        
        Returns:
            str: Resumen de la conversación.
        """
        if not self.conversation_history:
            return "No hay historial de conversación."
        
        summary = f"Resumen de la conversación ({len(self.conversation_history)} turnos):\n\n"
        
        for i, turn in enumerate(self.conversation_history, 1):
            summary += f"Turno {i}:\n"
            summary += f"  Usuario: \"{turn['user_text']}\"\n"
            summary += f"  Emoción: {turn['user_emotion']} ({turn['tone_score']:.1%})\n"
            summary += f"  Bot: \"{turn['bot_question']}\"\n\n"
        
        return summary
