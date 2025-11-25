"""
Script para ver exactamente qué se envía a Ollama.

Este script muestra el prompt completo que se construye y envía a Ollama.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nlp_cleaner import NLPContentCleaner

# Crear instancia del limpiador
cleaner = NLPContentCleaner(model_name="deepseek-r1:8b")

# Ejemplo de datos
title = "Nueva tecnología en inteligencia artificial"
summary = "Investigadores desarrollan un modelo de IA avanzado"
raw_content = """
Los investigadores de la Universidad de Stanford han desarrollado un nuevo modelo de inteligencia artificial.

El modelo utiliza técnicas de aprendizaje profundo para procesar lenguaje natural.

[Publicidad] ¿Quieres aprender Python? Inscríbete ahora.

Los resultados muestran mejoras significativas en comprensión de texto.

Este avance podría revolucionar múltiples campos de aplicación.

[Anuncio] Compra ahora con 50% de descuento.

Los investigadores planean publicar el código en los próximos meses.
"""

# Construir el prompt (usando el método privado, pero lo hacemos público para verlo)
print("=" * 70)
print("PROMPT QUE SE ENVÍA A OLLAMA")
print("=" * 70)
print()

prompt = cleaner._build_prompt(title, summary, raw_content)
print(prompt)

print("\n" + "=" * 70)
print("DETALLES DE LA PETICIÓN")
print("=" * 70)
print()
print(f"📤 URL: http://localhost:11434/api/generate")
print(f"🤖 Modelo: deepseek-r1:8b")
print(f"⏱️  Timeout: 300 segundos (5 minutos)")
print(f"📏 Longitud del prompt: {len(prompt)} caracteres")
print()
print("⚙️  Opciones de generación:")
print("   - temperature: 0.1 (muy baja para respuestas deterministas)")
print("   - num_predict: 2048 (máximo de tokens a generar)")
print("   - top_p: 0.9 (nucleus sampling)")
print("   - stream: False (respuesta completa de una vez)")
print()
print("📥 Respuesta esperada:")
print("   Un JSON con este formato:")
print("   {")
print('     "relevantes": ["párrafo 1", "párrafo 2"],')
print('     "irrelevantes": ["publicidad", "anuncio"],')
print('     "clean_text": "párrafo 1\\n\\npárrafo 2"')
print("   }")
print()
print("=" * 70)

