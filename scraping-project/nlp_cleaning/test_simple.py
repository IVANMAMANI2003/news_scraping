"""Test simple para verificar que Ollama responde correctamente"""
import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

from nlp_cleaner import clean_news

# Configurar logging para ver todo
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

# Datos de prueba
title = "Puno: Padrastro manoseó por años a hijastra"
summary = "El Poder Judicial de Juliaca ordenó prisión preventiva para Moisés Víctor Soncco, acusado de tocamientos indebidos a su hijastra de 16 años."
raw_content = """Las investigaciones revelan que los abusos sexuales empezaron cuando la niña tenía apenas nueve años, obligándola a vivir en silencio durante años a causa del miedo. LOS HECHOS Según la Fiscalía, el imputado aprovechaba la confianza que tenía con la adolescente de iniciales N.A.B., para cometer los abusos. La víctima declaró que el último abuso por parte de su padrastro ocurrió el jueves 24 de octubre del presente año. Según su testimonio, el sujeto ingresó a su habitación mientras dormía y procedió a manosearla. Asimismo, según la adolescente, los hechos se repitieron durante años, hasta que la víctima, cansada de los ataques, entre lágrimas, decidió contar primero a su tía toda la pesadilla que vivió durante siete años a manos de su padrastro. LA DENUNCIA Tras oír a su sobrina, junto a la madre de la agraviada decidieron acudir a la Policía y denunciar al sujeto. Es así que, el Ministerio Público logró que el juez dictara prisión preventiva contra el acusado, mientras continúan las investigaciones."""

print("=" * 70)
print("TEST SIMPLE - LIMPIEZA DE NOTICIAS CON OLLAMA")
print("=" * 70)
print()
print(f"📰 Título: {title}")
print(f"📝 Resumen: {summary}")
print(f"📄 Contenido RAW ({len(raw_content)} caracteres)")
print()
print("⏳ Enviando a Ollama...")
print()

# Llamar a la función de limpieza
try:
    result = clean_news(
        title=title,
        summary=summary,
        raw=raw_content
    )
    
    print("=" * 70)
    print("RESULTADO")
    print("=" * 70)
    print()
    print(f"✅ Oraciones relevantes: {len(result['relevantes'])}")
    print(f"❌ Oraciones irrelevantes: {len(result['irrelevantes'])}")
    print()
    
    if result['relevantes']:
        print("📌 ORACIONES RELEVANTES:")
        print("-" * 70)
        for i, oracion in enumerate(result['relevantes'][:5], 1):  # Mostrar solo las primeras 5
            print(f"{i}. {oracion[:100]}...")
        if len(result['relevantes']) > 5:
            print(f"... y {len(result['relevantes']) - 5} más")
        print()
    
    if result['irrelevantes']:
        print("🚫 ORACIONES IRRELEVANTES:")
        print("-" * 70)
        for i, oracion in enumerate(result['irrelevantes'][:3], 1):  # Mostrar solo las primeras 3
            print(f"{i}. {oracion[:100]}...")
        if len(result['irrelevantes']) > 3:
            print(f"... y {len(result['irrelevantes']) - 3} más")
        print()
    
    print("📄 TEXTO LIMPIO:")
    print("-" * 70)
    if result['clean_text']:
        print(result['clean_text'][:500])
        if len(result['clean_text']) > 500:
            print(f"\n... ({len(result['clean_text']) - 500} caracteres más)")
    else:
        print("⚠️ El texto limpio está vacío")
    print()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

