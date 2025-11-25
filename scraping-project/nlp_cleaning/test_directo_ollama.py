"""Test directo con Ollama - solo verificar que responde"""
import json

import ollama

print("=" * 70)
print("TEST DIRECTO CON OLLAMA")
print("=" * 70)
print()

# Crear cliente
client = ollama.Client()

# Prompt simple de prueba
title = "Puno: Padrastro manoseó por años a hijastra"
summary = "El Poder Judicial ordenó prisión preventiva"
content = "Las investigaciones revelan que los abusos empezaron cuando la niña tenía nueve años. Según la Fiscalía, el imputado aprovechaba la confianza."

prompt = f"""Analiza esta noticia y separa ORACIONES relevantes de irrelevantes.

Título: {title}
Resumen: {summary}
Contenido: {content}

Devuelve SOLO un JSON:
{{
  "relevantes": ["oración 1", "oración 2"],
  "irrelevantes": ["oración 3"],
  "clean_text": "oración 1\\noración 2"
}}"""

print("📤 Enviando prompt a Ollama...")
print(f"Modelo: deepseek-r1:8b")
print(f"Longitud del prompt: {len(prompt)} caracteres")
print()
print("⏳ Esperando respuesta...")
print()

try:
    print("🔄 Llamando a client.generate()...")
    # Enviar a Ollama
    response = client.generate(
        model='deepseek-r1:8b',
        prompt=prompt,
        options={
            "temperature": 0.1,
            "num_predict": 500,
        },
        stream=False
    )
    print("✅ Respuesta recibida de Ollama")
    
    print("=" * 70)
    print("RESPUESTA DE OLLAMA")
    print("=" * 70)
    print()
    
    # Mostrar tipo de respuesta
    print(f"Tipo de respuesta: {type(response)}")
    print()
    
    # Intentar extraer el contenido
    if hasattr(response, 'response'):
        response_text = response.response
        print(f"✅ Atributo 'response' encontrado")
        print(f"Longitud: {len(response_text)} caracteres")
        print()
        print("CONTENIDO:")
        print("-" * 70)
        print(response_text)
        print("-" * 70)
    else:
        print("⚠️ No se encontró atributo 'response'")
        print()
        print("Atributos disponibles:")
        if hasattr(response, '__dict__'):
            for attr, value in response.__dict__.items():
                if not attr.startswith('_'):
                    print(f"  - {attr}: {type(value)}")
                    if isinstance(value, str) and len(value) > 0:
                        print(f"    Valor: {value[:200]}...")
        else:
            print(f"  Respuesta completa: {response}")
    
    print()
    print("=" * 70)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

