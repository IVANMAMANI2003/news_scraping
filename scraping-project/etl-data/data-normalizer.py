import ast
import re
from datetime import datetime
from urllib.parse import urlparse

import numpy as np
import pandas as pd


class NewsETL:
    def __init__(self):
        self.processed_data = None
    
    def extract(self, file_path):
        """Extraer data del CSV"""
        try:
            df = pd.read_csv(file_path)
            print(f"✅ Data extraída: {len(df)} registros")
            return df
        except Exception as e:
            print(f"❌ Error en extracción: {e}")
            return None
    
    def transform(self, df):
        """Transformar la data"""
        # 1. Limpiar duplicados
        initial_count = len(df)
        df = df.drop_duplicates(subset=['id', 'url'], keep='first')
        print(f"📊 Duplicados eliminados: {initial_count - len(df)}")
        
        # 2. Procesar fechas
        df = self._process_dates(df)
        
        # 3. Procesar imágenes (separar URLs múltiples)
        df = self._process_images(df)
        
        # 4. Categorizar automáticamente
        df['categoria_auto'] = df.apply(
            lambda x: self._categorize_article(x['titulo'], x.get('contenido', '')), 
            axis=1
        )
        
        # 5. Extraer keywords
        df['keywords'] = df['titulo'].apply(self._extract_keywords)
        
        # 6. Limpiar URLs
        df['url_limpia'] = df['url'].apply(self._clean_url)
        df['dominio'] = df['url_limpia'].apply(self._extract_domain)
        
        # 7. Estandarizar fuente
        df['fuente_estandarizada'] = df['fuente'].apply(self._estandarizar_fuente)
        
        # 8. Calcular métricas de contenido
        df['longitud_titulo'] = df['titulo'].str.len().fillna(0)
        df['longitud_resumen'] = df['resumen'].str.len().fillna(0)
        
        # 9. Crear resumen si está vacío
        df = self._crear_resumen_automatico(df)
        
        # 10. Identificar tipo de contenido
        df['tipo_contenido'] = df.apply(self._identificar_tipo_contenido, axis=1)
        
        return df
    
    def _process_dates(self, df):
        """Procesar columnas de fecha"""
        df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['fecha_extraccion_dt'] = pd.to_datetime(df['fecha_extraccion'], errors='coerce')
        df['created_at_dt'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        # Extraer componentes de fecha
        df['anio'] = df['fecha_dt'].dt.year
        df['mes'] = df['fecha_dt'].dt.month
        df['dia'] = df['fecha_dt'].dt.day
        df['dia_semana'] = df['fecha_dt'].dt.day_name()
        df['semana_anio'] = df['fecha_dt'].dt.isocalendar().week
        
        return df
    
    def _process_images(self, df):
        """Procesar URLs de imágenes múltiples - solo conservar el primer link"""
        def obtener_primer_imagen(url_string):
            if pd.isna(url_string) or url_string == '':
                return None
            # Separar por punto y coma y tomar solo el primero
            urls = [url.strip() for url in str(url_string).split(';') if url.strip()]
            return urls[0] if urls else None
        
        def contar_imagenes(url_string):
            if pd.isna(url_string) or url_string == '':
                return 0
            # Contar cuántas imágenes hay separadas por ;
            urls = [url.strip() for url in str(url_string).split(';') if url.strip()]
            return len(urls)
        
        # Solo conservar el primer link de imagen
        df['imagen_principal'] = df['imagenes'].apply(obtener_primer_imagen)
        df['cantidad_imagenes'] = df['imagenes'].apply(contar_imagenes)
        df['tiene_imagenes'] = df['cantidad_imagenes'] > 0
        
        return df
    
    def _categorize_article(self, titulo, contenido):
        """Categorizar artículo basado en título y contenido"""
        if pd.isna(titulo):
            return 'Otros'
        
        text = f"{titulo} {contenido}".lower()
        
        categorias = {
            'Deportes': ['fútbol', 'futbol', 'partido', 'gol', 'liga', 'torneo', 'venc', 
                        'equipo', 'deportes', 'alianza', 'universitario', 'cusco fc'],
            'Política': ['congreso', 'fiscal', 'gobierno', 'polític', 'ministro', 'ley', 
                        'reforma', 'presidente', 'alcalde', 'funcionario', 'boluarte'],
            'Judicial': ['fiscalía', 'prisión', 'violación', 'crimen', 'delito', 'investigación',
                        'captura', 'robo', 'detención', 'asalto', 'policía'],
            'Social': ['protesta', 'huelga', 'social', 'conflicto', 'manifestación', 
                      'sutress', 'diresa', 'cuestionan', 'bloqueo'],
            'Economía': ['precio', 'económ', 'inversión', 'millones', 'gasto', 'déficit',
                        'comercio', 'viáticos', 'recursos', 'financiero'],
            'Salud': ['salud', 'anemia', 'hospital', 'médico', 'tratamiento', 'centros de salud'],
            'Medio Ambiente': ['contaminación', 'río', 'medio ambiente', 'relaves', 'miner',
                              'desborde', 'coata', 'cultivos'],
            'Turismo': ['turismo', 'embarcadero', 'titicaca', 'machu picchu', 'gira'],
            'Internacional': ['internacional', 'trump', 'hamás', 'paz', 'israel', 'irán',
                             'bolivia', 'donald', 'plan de paz'],
            'Ciencia': ['organismo', 'antiguo', 'científ', 'pando', 'huellas humanas',
                       'historia', 'años de antigüedad'],
            'Cultura': ['cultura', 'muestra', 'pictórica', 'patrón estético', 'artístico',
                       'encinas', 'instituto'],
            'Educación': ['educación', 'instituto', 'encinas', 'estudios', 'enseñanza']
        }
        
        for categoria, palabras in categorias.items():
            if any(palabra in text for palabra in palabras):
                return categoria
        
        return 'Otros'
    
    def _extract_keywords(self, titulo):
        """Extraer palabras clave del título"""
        if pd.isna(titulo):
            return []
        
        # Palabras comunes a excluir
        stop_words = {
            'de', 'la', 'el', 'en', 'y', 'a', 'los', 'las', 'del', 'se', 'con', 
            'por', 'para', 'su', 'al', 'lo', 'un', 'una', 'unos', 'unas', 'es', 'son',
            'que', 'como', 'más', 'pero', 'o', 'sin', 'sobre', 'bajo', 'entre'
        }
        
        palabras = re.findall(r'\b[a-zA-Záéíóúñ]{4,}\b', titulo.lower())
        keywords = [p for p in palabras if p not in stop_words]
        
        return keywords[:5]  # Máximo 5 keywords
    
    def _clean_url(self, url):
        """Limpiar URL"""
        if pd.isna(url):
            return url
        
        # Remover fragmentos
        url = url.split('#')[0]
        return url.strip()
    
    def _extract_domain(self, url):
        """Extraer dominio de URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return None
    
    def _estandarizar_fuente(self, fuente):
        """Estandarizar nombres de fuentes"""
        if pd.isna(fuente):
            return 'Desconocida'
        
        fuente_lower = str(fuente).lower()
        
        if 'pachamama' in fuente_lower:
            return 'Pachamama Radio'
        elif 'los_andes' in fuente_lower or 'andes' in fuente_lower:
            return 'Los Andes'
        elif 'puno' in fuente_lower and 'noticias' in fuente_lower:
            return 'Puno Noticias'
        else:
            return fuente.title()
    
    def _crear_resumen_automatico(self, df):
        """Crear resumen automático si está vacío"""
        mask = (df['resumen'].isna()) | (df['resumen'] == '')
        df.loc[mask, 'resumen'] = df.loc[mask, 'titulo'] + '. Información completa disponible en el contenido principal.'
        return df
    
    def _identificar_tipo_contenido(self, row):
        """Identificar tipo de contenido basado en características"""
        titulo = str(row['titulo']).lower()
        
        if any(word in titulo for word in ['?', '¿cómo', 'guía', 'práctica']):
            return 'Guía/Instructivo'
        elif any(word in titulo for word in ['anuncia', 'nuevo', 'lanzamiento']):
            return 'Anuncio'
        elif any(word in titulo for word in ['alerta', 'advierten', 'peligro']):
            return 'Alerta'
        elif any(word in titulo for word in ['investigación', 'estudio', 'descubrimiento']):
            return 'Investigación'
        elif row['cantidad_imagenes'] > 1:
            return 'Galería'
        else:
            return 'Noticia'
    
    def load(self, df, output_file):
        """Guardar data transformada"""
        # Preparar data para exportación
        df_export = df.copy()
        
        # Convertir listas a strings para CSV
        if 'keywords' in df_export.columns:
            df_export['keywords'] = df_export['keywords'].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            )
        
        # Las imágenes ya están procesadas como imagen_principal
        
        # Seleccionar columnas finales
        columnas_finales = [
            'id', 'titulo', 'fecha_dt', 'hora', 'anio', 'mes', 'dia', 'dia_semana',
            'resumen', 'contenido', 'categoria_auto', 'autor', 'keywords',
            'url_limpia', 'dominio', 'fecha_extraccion_dt', 'imagen_principal',
            'cantidad_imagenes', 'tiene_imagenes', 'fuente_estandarizada',
            'longitud_titulo', 'longitud_resumen', 'tipo_contenido', 'created_at_dt'
        ]
        
        # Filtrar columnas existentes
        columnas_existentes = [col for col in columnas_finales if col in df_export.columns]
        df_final = df_export[columnas_existentes]
        
        # Renombrar columnas para claridad
        rename_dict = {
            'fecha_dt': 'fecha',
            'fecha_extraccion_dt': 'fecha_extraccion',
            'created_at_dt': 'created_at',
            'url_limpia': 'url',
            'categoria_auto': 'categoria',
            'fuente_estandarizada': 'fuente'
        }
        df_final = df_final.rename(columns=rename_dict)
        
        # Guardar
        df_final.to_csv(output_file, index=False, encoding='utf-8')
        print(f"💾 Data transformada guardada en: {output_file}")
        
        return df_final
    
    def run_etl(self, input_file, output_file):
        """Ejecutar proceso ETL completo"""
        print("🚀 INICIANDO PROCESO ETL...")
        
        # EXTRACT
        df = self.extract(input_file)
        if df is None:
            return None
        
        # TRANSFORM
        df_transformado = self.transform(df)
        
        # LOAD
        df_final = self.load(df_transformado, output_file)
        
        self.processed_data = df_final
        return df_final

# Análisis y reportes
class DataAnalyzer:
    def __init__(self, df):
        self.df = df
    
    def generate_quality_report(self):
        """Generar reporte de calidad de datos"""
        print("\n" + "="*50)
        print("📊 REPORTE DE CALIDAD DE DATOS")
        print("="*50)
        
        print(f"📈 Total de registros: {len(self.df)}")
        print(f"📅 Rango de fechas: {self.df['fecha'].min()} a {self.df['fecha'].max()}")
        print(f"🏷️  Categorías únicas: {self.df['categoria'].nunique()}")
        print(f"📰 Fuentes únicas: {self.df['fuente'].nunique()}")
        
        print(f"\n✅ Completitud de datos:")
        print(f"   - Títulos: {self.df['titulo'].notna().sum()} ({self.df['titulo'].notna().mean()*100:.1f}%)")
        print(f"   - Fechas: {self.df['fecha'].notna().sum()} ({self.df['fecha'].notna().mean()*100:.1f}%)")
        print(f"   - URLs: {self.df['url'].notna().sum()} ({self.df['url'].notna().mean()*100:.1f}%)")
        print(f"   - Imágenes: {self.df['tiene_imagenes'].sum()} ({self.df['tiene_imagenes'].mean()*100:.1f}%)")
        
        print(f"\n📊 Distribución por categoría:")
        for categoria, count in self.df['categoria'].value_counts().items():
            print(f"   - {categoria}: {count} ({count/len(self.df)*100:.1f}%)")
        
        print(f"\n📰 Distribución por fuente:")
        for fuente, count in self.df['fuente'].value_counts().items():
            print(f"   - {fuente}: {count} ({count/len(self.df)*100:.1f}%)")
    
    def generate_content_analysis(self):
        """Análisis de contenido"""
        print(f"\n📝 ANÁLISIS DE CONTENIDO")
        print(f"   - Longitud promedio de títulos: {self.df['longitud_titulo'].mean():.1f} caracteres")
        print(f"   - Longitud promedio de resúmenes: {self.df['longitud_resumen'].mean():.1f} caracteres")
        print(f"   - Imágenes por artículo: {self.df['cantidad_imagenes'].mean():.1f}")
        
        print(f"\n🎯 Tipos de contenido:")
        for tipo, count in self.df['tipo_contenido'].value_counts().items():
            print(f"   - {tipo}: {count}")

# Ejecutar el ETL
if __name__ == "__main__":
    # Configuración
    input_file = "noticias_20251014_062537.csv"  # Tu archivo actual
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data_etl_final_{timestamp}.csv"
    
    # Ejecutar ETL
    etl = NewsETL()
    df_final = etl.run_etl(input_file, output_file)
    
    if df_final is not None:
        # Generar reportes
        analyzer = DataAnalyzer(df_final)
        analyzer.generate_quality_report()
        analyzer.generate_content_analysis()
        
        # Mostrar sample
        print(f"\n🔍 SAMPLE DE DATA TRANSFORMADA:")
        print(df_final[['id', 'titulo', 'categoria', 'fuente', 'fecha']].head(10).to_string(index=False))