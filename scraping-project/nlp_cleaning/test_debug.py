"""Test de debugging - ver exactamente qué devuelve Ollama"""
import time

import ollama

print("=" * 70)
print("TEST DEBUG - OLLAMA")
print("=" * 70)
print()

client = ollama.Client()

# Prompt muy corto para que responda rápido
prompt = "Di 'Hola' en una palabra"

print(f"📤 Prompt: {prompt}")
print(f"🤖 Modelo: deepseek-r1:8b")
print()
print("⏳ Enviando...")
start_time = time.time()

try:
    response = client.generate(
        model='deepseek-r1:8b',
        prompt=prompt,
        options={"num_predict": 10},  # Solo 10 tokens
        stream=False
    )
    
    elapsed = time.time() - start_time
    print(f"✅ Respuesta recibida en {elapsed:.2f} segundos")
    print()
    print("=" * 70)
    print("ANÁLISIS DE LA RESPUESTA")
    print("=" * 70)
    print()
    
    print(f"Tipo de objeto: {type(response)}")
    print(f"Es dict: {isinstance(response, dict)}")
    print()
    
    # Verificar atributos
    print("Atributos del objeto:")
    if hasattr(response, '__dict__'):
        for attr_name in dir(response):
            if not attr_name.startswith('_'):
                try:
                    attr_value = getattr(response, attr_name)
                    attr_type = type(attr_value).__name__
                    if isinstance(attr_value, str):
                        print(f"  ✅ {attr_name}: {attr_type} = '{attr_value[:100]}'")
                    else:
                        print(f"  - {attr_name}: {attr_type}")
                except:
                    print(f"  ⚠️ {attr_name}: (error al acceder)")
    else:
        print("  No tiene __dict__")
    
    print()
    print("=" * 70)
    print("EXTRAYENDO RESPUESTA")
    print("=" * 70)
    print()
    
    # Intentar extraer respuesta
    response_text = None
    
    if hasattr(response, 'response'):
        response_text = response.response
        print(f"✅ Encontrado en response.response")
    elif hasattr(response, 'text'):
        response_text = response.text
        print(f"✅ Encontrado en response.text")
    elif isinstance(response, dict):
        response_text = response.get('response', '') or response.get('text', '')
        print(f"✅ Encontrado en dict['response'] o dict['text']")
    
    if response_text:
        print(f"✅ TEXTO EXTRAÍDO: {len(response_text)} caracteres")
        print()
        print("CONTENIDO:")
        print("-" * 70)
        print(response_text)
        print("-" * 70)
    else:
        print("❌ NO SE PUDO EXTRAER TEXTO")
        print()
        print("Objeto completo:")
        print(response)
    
except Exception as e:
    elapsed = time.time() - start_time
    print(f"❌ ERROR después de {elapsed:.2f} segundos: {e}")
    import traceback
    traceback.print_exc()

