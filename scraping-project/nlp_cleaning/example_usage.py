"""
Ejemplo de uso del módulo de limpieza de noticias con Ollama.

Este script muestra cómo usar el módulo para limpiar contenido de noticias.
"""

from nlp_cleaner import NLPContentCleaner, clean_news

# Ejemplo 1: Uso básico con la función clean_news()
print("=" * 60)
print("Ejemplo 1: Uso básico con clean_news()")
print("=" * 60)

title = "Nueva tecnología en inteligencia artificial revoluciona el procesamiento de lenguaje"
summary = "Investigadores presentan un modelo de IA que puede entender y generar texto con precisión humana"
raw_content = """
Los investigadores de la Universidad de Stanford han desarrollado un nuevo modelo de inteligencia artificial 
que promete revolucionar la forma en que las máquinas procesan el lenguaje natural.

El modelo, llamado GPT-Advanced, utiliza técnicas de aprendizaje profundo para entender el contexto 
y generar respuestas coherentes y precisas.

[Publicidad] ¿Quieres aprender Python? Inscríbete en nuestro curso online ahora mismo.

Los resultados de las pruebas muestran que el modelo supera a los sistemas anteriores en tareas 
de comprensión de lectura y generación de texto.

Este avance podría tener aplicaciones en múltiples campos, desde asistentes virtuales hasta 
sistemas de traducción automática.

[Anuncio] Compra ahora y obtén un 50% de descuento en todos nuestros productos.

Los investigadores planean hacer el modelo disponible para la comunidad científica en los próximos meses.
"""

print("\n📤 Enviando petición a Ollama...")
print("   (Asegúrate de que Ollama esté corriendo y el modelo deepseek-r1:8b esté disponible)")

result = clean_news(
    title=title,
    summary=summary,
    raw=raw_content
)

print(f"\n📊 Resultados:")
print(f"   Párrafos relevantes: {len(result['relevantes'])}")
print(f"   Párrafos irrelevantes: {len(result['irrelevantes'])}")

print(f"\n✅ Párrafos relevantes seleccionados:")
for i, para in enumerate(result['relevantes'], 1):
    print(f"\n   {i}. {para[:100]}...")

print(f"\n❌ Párrafos irrelevantes filtrados:")
for i, para in enumerate(result['irrelevantes'], 1):
    print(f"\n   {i}. {para[:100]}...")

print(f"\n📄 Texto limpio (párrafos relevantes unidos):")
print("-" * 60)
print(result['clean_text'])
print("-" * 60)

# Ejemplo 2: Uso con la clase NLPContentCleaner
print("\n\n" + "=" * 60)
print("Ejemplo 2: Uso con NLPContentCleaner")
print("=" * 60)

cleaner = NLPContentCleaner(
    model_name="deepseek-r1:8b"
)

result2 = cleaner.clean_news(
    title="Noticia de ejemplo",
    summary="Resumen de la noticia",
    raw="Párrafo 1 relevante.\n\nPárrafo 2 también relevante.\n\n[Publicidad] No relevante."
)

print(f"\n📊 Párrafos procesados:")
print(f"   Relevantes: {len(result2['relevantes'])}")
print(f"   Irrelevantes: {len(result2['irrelevantes'])}")
print(f"\n📄 Texto limpio:")
print(result2['clean_text'])

print("\n✅ Ejemplos completados!")
print("\n💡 Nota: Asegúrate de tener Ollama corriendo:")
print("   1. Instalar Ollama: https://ollama.ai")
print("   2. Descargar modelo: ollama pull deepseek-r1:8b")
print("   3. Verificar: ollama list")
