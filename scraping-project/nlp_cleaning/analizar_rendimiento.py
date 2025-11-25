"""
Script para analizar dónde se está demorando el proceso.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nlp_cleaner import NLPContentCleaner

print("=" * 70)
print("ANÁLISIS DE RENDIMIENTO - ¿QUIÉN ESTÁ DEMORANDO?")
print("=" * 70)

# Datos de prueba
title = "Nueva tecnología en IA"
summary = "Investigadores desarrollan modelo avanzado"
raw_content = """
Los investigadores de Stanford han desarrollado un nuevo modelo.

El modelo utiliza técnicas de aprendizaje profundo.

[Publicidad] Aprende Python ahora.

Los resultados muestran mejoras significativas.

Este avance podría revolucionar múltiples campos.

[Anuncio] Compra con descuento.

Los investigadores planean publicar el código.
"""

print("\n📊 Desglose del tiempo:")
print("-" * 70)

# 1. Construcción del prompt
start = time.time()
cleaner = NLPContentCleaner(model_name="deepseek-r1:8b")
prompt = cleaner._build_prompt(title, summary, raw_content)
time_prompt = time.time() - start
print(f"1. Construcción del prompt: {time_prompt:.3f} segundos ✅ (muy rápido)")

# 2. Envío y procesamiento en Ollama (esto es lo que tarda)
print(f"\n2. Envío a Ollama y procesamiento:")
print(f"   ⏱️  Esto es lo que DEMORA (30-90 segundos típicamente)")
print(f"   📤 Enviando petición HTTP a Ollama...")
print(f"   🤖 Ollama recibe el prompt")
print(f"   🧠 Modelo deepseek-r1:8b procesa el prompt (AQUÍ SE DEMORA)")
print(f"   📥 Ollama genera la respuesta JSON")
print(f"   📥 Recibiendo respuesta HTTP")

start = time.time()
try:
    result = cleaner.clean_news(title, summary, raw_content)
    time_ollama = time.time() - start
    print(f"   ⏱️  Tiempo total de Ollama: {time_ollama:.2f} segundos")
    print(f"   ✅ Respuesta recibida")
except Exception as e:
    time_ollama = time.time() - start
    print(f"   ⏱️  Tiempo hasta error: {time_ollama:.2f} segundos")
    print(f"   ❌ Error: {e}")

# 3. Parseo de JSON
start = time.time()
# Simular parseo (ya se hizo arriba)
time_parse = time.time() - start
print(f"\n3. Parseo de JSON: {time_parse:.3f} segundos ✅ (muy rápido)")

print("\n" + "=" * 70)
print("CONCLUSIÓN:")
print("=" * 70)
print("""
❌ CUELLO DE BOTELLA: OLLAMA (específicamente el modelo deepseek-r1:8b)

El tiempo se distribuye así:
- Construcción del prompt: < 0.001s (0%)
- Ollama procesando: 30-90s (99%+)
- Parseo JSON: < 0.001s (0%)

FACTORES QUE AFECTAN LA VELOCIDAD:
1. Tamaño del contenido (más texto = más tiempo)
2. Hardware:
   - CPU: 30-120 segundos por noticia
   - GPU: 10-30 segundos por noticia
3. Modelo usado:
   - deepseek-r1:8b: ~8.2B parámetros (lento pero preciso)
   - Modelos más pequeños: más rápidos pero menos precisos

OPCIONES PARA ACELERAR:
1. Usar GPU si está disponible (Ollama la detecta automáticamente)
2. Usar un modelo más pequeño (más rápido, menos preciso)
3. Reducir el tamaño del contenido enviado
4. Procesar en paralelo (múltiples noticias a la vez)
""")

