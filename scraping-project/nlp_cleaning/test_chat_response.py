"""Script para probar la respuesta de Ollama chat"""
import json

import ollama

client = ollama.Client()

# Prueba simple
print("Probando chat con prompt simple...")
try:
    resp = client.chat(
        model='deepseek-r1:8b',
        messages=[
            {
                "role": "user",
                "content": "Say hello in one word"
            }
        ],
        options={
            "num_predict": 50,
        }
    )
    
    print(f"\nTipo de respuesta: {type(resp)}")
    print(f"Tiene 'message': {hasattr(resp, 'message')}")
    
    if hasattr(resp, 'message'):
        print(f"Tipo de message: {type(resp.message)}")
        if hasattr(resp.message, 'content'):
            print(f"message.content: {repr(resp.message.content)}")
        elif isinstance(resp.message, dict):
            print(f"message (dict): {resp.message}")
        else:
            print(f"message (otro): {resp.message}")
            if hasattr(resp.message, '__dict__'):
                print(f"Atributos de message: {list(resp.message.__dict__.keys())}")
    
    # Intentar otros métodos
    if hasattr(resp, '__dict__'):
        print(f"\nAtributos de respuesta: {list(resp.__dict__.keys())}")
    
    # Intentar como dict
    if isinstance(resp, dict):
        print(f"Claves: {list(resp.keys())}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

