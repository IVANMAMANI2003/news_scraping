"""Test rápido - verificar respuesta de Ollama con timeout"""
import signal
import sys

import ollama


def timeout_handler(signum, frame):
    print("\n⏱️  Timeout alcanzado (60 segundos)")
    print("El modelo está tardando mucho. Esto puede ser normal para deepseek-r1:8b")
    sys.exit(1)

# Configurar timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60 segundos

print("=" * 70)
print("TEST RÁPIDO - OLLAMA")
print("=" * 70)
print()

client = ollama.Client()

# Prompt muy simple
prompt = """Analiza esta noticia:

Título: Test
Resumen: Test resumen
Contenido: Esta es una oración de prueba. Esta es otra oración.

Devuelve JSON:
{"relevantes": ["oración"], "irrelevantes": [], "clean_text": "texto"}"""

print("📤 Enviando a Ollama...")
print("Modelo: deepseek-r1:8b")
print("⏳ Esperando (máximo 60 segundos)...")
print()

try:
    response = client.generate(
        model='deepseek-r1:8b',
        prompt=prompt,
        options={"num_predict": 200},
        stream=False
    )
    
    signal.alarm(0)  # Cancelar timeout
    
    print("✅ RESPUESTA RECIBIDA")
    print("=" * 70)
    print()
    
    if hasattr(response, 'response'):
        texto = response.response
        print(f"✅ Contenido encontrado: {len(texto)} caracteres")
        print()
        print("RESPUESTA:")
        print("-" * 70)
        print(texto)
        print("-" * 70)
    else:
        print("⚠️ No se encontró 'response'")
        print(f"Tipo: {type(response)}")
        if hasattr(response, '__dict__'):
            print("Atributos:")
            for k, v in response.__dict__.items():
                if not k.startswith('_'):
                    print(f"  {k}: {type(v)}")
                    if isinstance(v, str) and v:
                        print(f"    -> {v[:100]}")
        
except KeyboardInterrupt:
    signal.alarm(0)
    print("\n⚠️  Cancelado por el usuario")
except Exception as e:
    signal.alarm(0)
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

