#!/usr/bin/env python3
"""
Script de prueba para verificar la extracción de imágenes del spider de Los Andes
Genera un CSV con los links de imagen encontrados
"""

import os
import sys
from datetime import datetime

# Agregar el directorio de spiders al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from spiders.losandes_local import LosAndesLocalScraper


def test_image_extraction():
    """Prueba la extracción de imágenes de algunos artículos"""
    print("=" * 70)
    print("🧪 PRUEBA DE EXTRACCIÓN DE IMÁGENES - LOS ANDES")
    print("=" * 70)
    
    scraper = LosAndesLocalScraper()
    
    # Obtener algunos artículos de la página principal (solo para prueba)
    print("\n📰 Obteniendo artículos de la página principal...")
    article_urls = scraper.get_article_links_from_page(scraper.base_url)
    
    # Limitar a los primeros 5 artículos para la prueba (más rápido)
    test_urls = article_urls[:5] if len(article_urls) >= 5 else article_urls
    
    print(f"✅ Encontrados {len(article_urls)} artículos")
    print(f"📊 Procesando {len(test_urls)} artículos para la prueba...\n")
    
    # Crear nombre de archivo una sola vez
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"data/losandes/test_imagenes_{timestamp}.csv"
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    results = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"[{i}/{len(test_urls)}] Procesando: {url}")
        
        try:
            article_data = scraper.extract_article_data(url)
            
            if article_data:
                # Separar las imágenes en columnas individuales
                images = article_data.get('imagenes', '').split(', ') if article_data.get('imagenes') else []
                
                result_row = {
                    'URL_Articulo': url,
                    'Titulo': article_data.get('titulo', ''),
                    'Fecha': article_data.get('fecha', ''),
                    'Categoria': article_data.get('categoria', ''),
                    'Num_Imagenes': len(images),
                    'Imagen_1': images[0] if len(images) > 0 else '',
                    'Imagen_2': images[1] if len(images) > 1 else '',
                    'Todas_Imagenes': article_data.get('imagenes', ''),
                    'Tipo_Extraccion': 'img_tag' if images else 'background_css' if any('background' in img.lower() for img in images) else 'unknown'
                }
                
                results.append(result_row)
                
                # Guardar incrementalmente después de cada artículo
                if results:
                    df_temp = pd.DataFrame(results)
                    df_temp.to_csv(csv_file, index=False, encoding='utf-8-sig')
                
                # Mostrar resumen
                if images:
                    print(f"   ✅ {len(images)} imagen(es) encontrada(s):")
                    for idx, img in enumerate(images, 1):
                        print(f"      [{idx}] {img}")
                else:
                    print(f"   ⚠️  No se encontraron imágenes")
            else:
                print(f"   ❌ No se pudo extraer el artículo")
                results.append({
                    'URL_Articulo': url,
                    'Titulo': 'ERROR',
                    'Fecha': '',
                    'Categoria': '',
                    'Num_Imagenes': 0,
                    'Imagen_1': '',
                    'Imagen_2': '',
                    'Todas_Imagenes': '',
                    'Tipo_Extraccion': 'error'
                })
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                'URL_Articulo': url,
                'Titulo': f'ERROR: {str(e)}',
                'Fecha': '',
                'Categoria': '',
                'Num_Imagenes': 0,
                'Imagen_1': '',
                'Imagen_2': '',
                'Todas_Imagenes': '',
                'Tipo_Extraccion': 'error'
            })
        
        print()
    
    # Crear DataFrame y guardar en CSV (guardado final)
    if results:
        df = pd.DataFrame(results)
        
        # Guardar en CSV con encoding UTF-8 (ya existe el archivo, se sobrescribe)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        print("=" * 70)
        print("✅ PRUEBA COMPLETADA")
        print("=" * 70)
        print(f"\n📊 Estadísticas:")
        print(f"   - Total de artículos procesados: {len(results)}")
        print(f"   - Artículos con imágenes: {sum(1 for r in results if r['Num_Imagenes'] > 0)}")
        print(f"   - Total de imágenes encontradas: {sum(r['Num_Imagenes'] for r in results)}")
        print(f"\n📁 Archivo CSV generado:")
        print(f"   {csv_file}")
        print(f"\n💡 Abre el archivo CSV para ver todos los links de imagen")
        
        return csv_file
    else:
        print("❌ No se obtuvieron resultados")
        return None


if __name__ == "__main__":
    try:
        csv_file = test_image_extraction()
        if csv_file:
            print(f"\n✅ ¡Prueba exitosa! Archivo guardado en: {csv_file}")
        else:
            print("\n❌ La prueba no generó resultados")
    except Exception as e:
        print(f"\n❌ Error en la prueba: {str(e)}")
        import traceback
        traceback.print_exc()

