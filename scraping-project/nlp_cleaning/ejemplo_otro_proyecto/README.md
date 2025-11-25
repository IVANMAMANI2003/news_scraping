# Módulo Bot Dinámico con IA

Este módulo proporciona un bot conversacional inteligente que integra análisis de voz con generación de preguntas adaptativas usando Ollama.

## 🎯 Características

- **Captura de voz en tiempo real** desde el micrófono
- **Análisis completo de voz** usando `voice_ai_module`:
  - Transcripción de voz a texto (STT) con Whisper
  - Análisis de emoción por voz (SER) con HuBERT
  - Fusión de resultados
- **Generación de preguntas adaptativas** usando Ollama (deepseek-r1)
- **Conversaciones empáticas** basadas en el estado emocional del usuario
- **Historial de conversación** para contexto

## 📁 Estructura del Módulo

```
bot_dynamic/
├── __init__.py          # Inicialización del módulo
├── bot.py               # Bot conversacional principal
├── ollama_client.py     # Cliente para Ollama API
├── requirements.txt     # Dependencias del módulo
└── README.md           # Este archivo
```

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install -r models/bot_dynamic/requirements.txt
```

### 2. Instalar dependencias de voice_ai_module

```bash
pip install -r models/voice_ai_module/requirements.txt
```

### 3. Instalar y configurar Ollama

**⚠️ IMPORTANTE:** Ollama debe estar instalado y ejecutándose.

Si Ollama no está instalado, consulta la guía: [INSTALL_OLLAMA.md](../../INSTALL_OLLAMA.md)

**Pasos rápidos:**
```bash
# 1. Descargar e instalar Ollama desde: https://ollama.com/download

# 2. Verificar que Ollama esté corriendo
curl http://localhost:11434/api/tags

# 3. Descargar el modelo deepseek-r1
ollama pull deepseek-r1
```

### 4. Verificar instalación

```bash
python test_bot_dynamic.py
```

## 📖 Uso Básico

### Ejemplo 1: Conversación simple

```python
from models.bot_dynamic import DynamicBot

# Inicializar bot
bot = DynamicBot(
    ollama_url="http://localhost:11434",
    ollama_model="deepseek-r1",
    record_duration=5.0
)

# Realizar conversación (3 turnos)
conversation = bot.converse(num_turns=3)

# Ver resumen
print(bot.get_conversation_summary())
```

### Ejemplo 2: Captura y análisis individual

```python
from models.bot_dynamic import DynamicBot

bot = DynamicBot()

# Capturar y analizar respuesta del usuario
analysis = bot.capture_and_analyze(duration=5.0)

print(f"Texto: {analysis['transcription']}")
print(f"Emoción: {analysis['voice_emotion_tone']}")

# Generar pregunta adaptativa
question = bot.generate_question(
    user_text=analysis['transcription'],
    user_emotion=analysis['voice_emotion_tone']
)

print(f"Pregunta: {question}")
```

### Ejemplo 3: Uso del cliente Ollama directamente

```python
from models.bot_dynamic import OllamaClient

client = OllamaClient(model="deepseek-r1")

# Generar pregunta adaptativa
question = client.generate_adaptive_question(
    user_text="Me siento muy triste hoy",
    user_emotion="sad"
)

print(question)
```

## 🔧 Componentes

### DynamicBot

Clase principal del bot conversacional.

**Métodos principales:**
- `capture_and_analyze(duration)`: Captura y analiza audio del usuario
- `generate_question(user_text, user_emotion, context)`: Genera pregunta adaptativa
- `converse(num_turns, duration)`: Realiza una conversación completa
- `get_conversation_summary()`: Obtiene resumen de la conversación

### OllamaClient

Cliente para comunicarse con Ollama API.

**Métodos principales:**
- `generate(prompt, system_prompt, stream)`: Genera respuesta con Ollama
- `chat(messages, stream)`: Realiza conversación en formato chat
- `generate_adaptive_question(user_text, user_emotion, context)`: Genera pregunta adaptativa

## ⚙️ Configuración

### Parámetros del Bot

- `ollama_url`: URL de Ollama API (por defecto: "http://localhost:11434")
- `ollama_model`: Modelo de Ollama a utilizar (por defecto: "deepseek-r1")
- `sample_rate`: Tasa de muestreo del audio (por defecto: 16000)
- `record_duration`: Duración de grabación por defecto (por defecto: 5.0 segundos)

### Modelos Ollama Soportados

El bot está diseñado para usar `deepseek-r1`, pero puede funcionar con otros modelos:
- `deepseek-r1` (recomendado)
- `llama3`
- `mistral`
- Cualquier otro modelo compatible con Ollama

## 📊 Formato de Resultados

### Análisis de Voz

```python
{
    "transcription": "Texto transcrito",
    "voice_emotion_tone": "happy",
    "tone_score": 0.85,
    "all_tone_scores": {...},
    "combined_emotion": "Análisis combinado"
}
```

### Turno de Conversación

```python
{
    "turn": 1,
    "user_text": "Texto del usuario",
    "user_emotion": "sad",
    "tone_score": 0.75,
    "bot_question": "Pregunta generada",
    "analysis": {...}
}
```

## 🎤 Flujo de Conversación

1. **Captura**: El bot graba audio del usuario (5 segundos por defecto)
2. **Análisis**: 
   - Transcripción de voz a texto (STT)
   - Detección de emoción por voz (SER)
   - Fusión de resultados
3. **Generación**: 
   - Envío a Ollama con contexto emocional
   - Generación de pregunta adaptativa
4. **Respuesta**: El bot presenta la pregunta al usuario
5. **Repetición**: El proceso se repite para cada turno

## 🔍 Prompt para Ollama

El bot utiliza el siguiente prompt para generar preguntas adaptativas:

```
Eres un asistente empático que conversa con un usuario.
El usuario acaba de decir: "{user_text}"
Su emoción percibida por voz es: "{user_emotion}"
Genera una pregunta empática y coherente basada en esto.
```

## 🧪 Pruebas

Ejecutar el script de prueba:

```bash
python test_bot_dynamic.py
```

Este script:
1. Inicializa el bot
2. Realiza 3 turnos de conversación
3. Muestra un resumen completo

## 📝 Notas

- **Ollama debe estar ejecutándose** antes de usar el bot
- El modelo `deepseek-r1` debe estar descargado en Ollama
- La primera ejecución puede tardar mientras se cargan los modelos
- El bot está configurado para español por defecto

## 🔍 Troubleshooting

### Error: "No se pudo conectar a Ollama"
- Verificar que Ollama esté ejecutándose: `ollama serve`
- Verificar la URL: `http://localhost:11434`

### Error: "Modelo 'deepseek-r1' no encontrado"
- Descargar el modelo: `ollama pull deepseek-r1`
- Verificar modelos disponibles: `ollama list`

### Error: "Timeout al generar respuesta"
- Aumentar el timeout en `OllamaClient(timeout=120)`
- Verificar que el modelo esté cargado correctamente

### Error: "No se encontraron dispositivos de audio"
- Verificar que el micrófono esté conectado
- Verificar permisos de acceso al micrófono

## 📚 Referencias

- [Ollama Documentation](https://github.com/ollama/ollama)
- [DeepSeek R1](https://www.deepseek.com/)
- [voice_ai_module](../voice_ai_module/README.md)

## 📄 Licencia

Este módulo es parte del proyecto de sistema de asistencia UPEU.
