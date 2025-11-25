"""
Router para gestión de scrapers
Permite ejecutar scrapers de noticias desde la API
"""

import asyncio
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

# Agregar el directorio raíz al path para importar scrapers
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# Importar conexión a base de datos
from ..db import get_conn, put_conn


# Pre-configurar mocks de dependencias ANTES de que se importen los scrapers
# Esto evita errores de importación cuando las dependencias no están instaladas
def setup_dependency_mocks():
    """Configura mocks de dependencias opcionales antes de importar scrapers"""
    import types

    # Mock de pandas
    if 'pandas' not in sys.modules:
        try:
            import pandas
        except ImportError:
            pandas_mock = types.ModuleType('pandas')
            pandas_mock.__version__ = '2.0.0'
            
            class DataFrameMock:
                def __init__(self, data):
                    self.data = data if data else []
                def to_csv(self, *args, **kwargs):
                    pass
                def __len__(self):
                    return len(self.data) if self.data else 0
            
            pandas_mock.DataFrame = DataFrameMock
            pandas_mock.pd = pandas_mock
            sys.modules['pandas'] = pandas_mock
    
    # Mock de bs4 (BeautifulSoup4) - CRÍTICO para scrapers
    # IMPORTANTE: Los scrapers hacen "from bs4 import BeautifulSoup" al inicio
    # Por lo tanto, bs4 debe estar en sys.modules ANTES de importar cualquier scraper
    if 'bs4' not in sys.modules:
        try:
            # Intentar importar bs4 real
            import bs4
            from bs4 import BeautifulSoup

            # Si funciona, no necesitamos mock
        except (ImportError, ModuleNotFoundError):
            # Crear mock completo de bs4
            bs4_mock = types.ModuleType('bs4')
            bs4_mock.__name__ = 'bs4'
            bs4_mock.__package__ = 'bs4'
            
            # Crear clase BeautifulSoup mock más completa
            class BeautifulSoupMock:
                def __init__(self, markup=None, features=None, **kwargs):
                    self.markup = markup
                    self.features = features or 'html.parser'
                    self.contents = []
                    self.string = ''
                def find_all(self, *args, **kwargs):
                    return []
                def find(self, *args, **kwargs):
                    return None
                def select(self, *args, **kwargs):
                    return []
                def select_one(self, *args, **kwargs):
                    return None
                def get(self, *args, **kwargs):
                    return None
                def __getattr__(self, name):
                    # Retornar None para cualquier atributo que no exista
                    return None
                def __getitem__(self, key):
                    return None
            
            # Asignar BeautifulSoup al módulo
            bs4_mock.BeautifulSoup = BeautifulSoupMock
            
            # Registrar en sys.modules - CRÍTICO: debe estar antes de cualquier import
            sys.modules['bs4'] = bs4_mock
            sys.modules['bs4.BeautifulSoup'] = BeautifulSoupMock
            
            # También asegurar que 'BeautifulSoup' esté disponible directamente
            # para imports como "from bs4 import BeautifulSoup"
            import builtins
            if not hasattr(builtins, 'BeautifulSoup'):
                builtins.BeautifulSoup = BeautifulSoupMock

# Ejecutar setup de mocks al importar el módulo
setup_dependency_mocks()

router = APIRouter()

# Estado global de scraping
scraping_status: Dict[str, Dict] = {}


class ScrapingRequest(BaseModel):
    """Modelo para solicitud de scraping"""
    type: str  # complete, selected, single, date, today, yesterday, week, month, dateRange
    sources: Optional[List[str]] = None
    source: Optional[str] = None
    date: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    limit: Optional[int] = None  # Límite de noticias a extraer (5, 10, 20, None = sin límite)
    categoria: Optional[str] = None  # Filtrar por categoría específica


class ScrapingResponse(BaseModel):
    """Modelo para respuesta de scraping"""
    job_id: str
    status: str
    message: str
    timestamp: str


class ScrapingStatusResponse(BaseModel):
    """Modelo para estado de scraping"""
    job_id: str
    status: str  # running, completed, error
    progress: float
    current_source: Optional[str] = None
    results: List[Dict] = []
    logs: List[str] = []
    timestamp: str


# Mapeo de fuentes a módulos
SOURCE_MAPPING = {
    "pachamama": {
        "module": "spiders.pachamamaradio_local",
        "function": "main",
        "name": "Pachamama Radio"
    },
    "punonoticias": {
        "module": "spiders.punonoticias_local",
        "function": "main",
        "name": "Puno Noticias"
    },
    "losandes": {
        "module": "spiders.losandes_local",
        "function": "main",
        "name": "Los Andes"
    },
    "sinfronteras": {
        "module": "spiders.sinfronteras_local",
        "function": "main",
        "name": "Sin Fronteras"
    }
    # Scraper de prueba deshabilitado
    # "test": {
    #     "module": "spiders.test_scraper_local",
    #     "function": "main",
    #     "name": "Test Scraper"
    # }
}


def insert_news_to_database(news_data: List[Dict], source_name: str) -> int:
    """
    Inserta noticias en la tabla 'noticias' (no noticias_limpia)
    Retorna el número de noticias insertadas
    """
    conn = get_conn()
    if not conn:
        raise Exception("No se pudo obtener conexión a la base de datos")
    
    inserted_count = 0
    skipped_no_url = 0
    skipped_duplicate = 0
    error_count = 0
    
    print(f"[DEBUG] Procesando {len(news_data)} artículos para inserción...")
    
    try:
        cursor = conn.cursor()
        
        for idx, article in enumerate(news_data):
            try:
                # Verificar si ya existe por URL (ÚNICO criterio para evitar duplicados)
                url = article.get('url') or article.get('link') or article.get('href')
                if not url:
                    skipped_no_url += 1
                    if idx < 5:  # Log solo los primeros 5 para no saturar
                        print(f"[DEBUG] Artículo {idx} sin URL, saltando")
                    continue
                
                # Normalizar URL: eliminar trailing slash y espacios
                url = url.strip().rstrip('/')
                
                # Verificar duplicados por URL (comparación exacta)
                cursor.execute("SELECT id FROM noticias WHERE url = %s", (url,))
                if cursor.fetchone():
                    skipped_duplicate += 1
                    if idx < 5:  # Log solo los primeros 5 para no saturar
                        print(f"[DEBUG] Artículo {idx} ya existe (URL duplicada: {url[:50]}...), saltando")
                    continue  # Ya existe por URL, no insertar
                
                # Preparar datos para inserción
                contenido = article.get('contenido') or article.get('content') or article.get('texto') or ''
                resumen = article.get('resumen') or article.get('summary') or article.get('excerpt') or ''
                titulo = article.get('titulo') or article.get('title') or 'Sin título'
                categoria = article.get('categoria') or article.get('category') or 'General'
                autor = article.get('autor') or article.get('author') or ''
                tags = article.get('tags') or article.get('keywords') or ''
                
                # Manejar fecha
                fecha = article.get('fecha') or article.get('date')
                if fecha:
                    if isinstance(fecha, str):
                        try:
                            from dateutil import parser
                            fecha = parser.parse(fecha).date()
                        except:
                            fecha = None
                    elif hasattr(fecha, 'date'):
                        fecha = fecha.date()
                
                # Manejar imagenes
                imagenes = article.get('imagenes') or article.get('images') or article.get('imagen_principal') or ''
                if isinstance(imagenes, list):
                    imagenes = ','.join(imagenes)
                
                # Insertar en tabla noticias (usar esquema según init.sql)
                # La tabla tiene: id, titulo, fecha, hora, resumen, contenido, categoria, autor, tags, url, fecha_extraccion, imagenes, fuente, created_at
                insert_query = """
                INSERT INTO noticias (
                    titulo, fecha, resumen, contenido, categoria, autor, 
                    tags, url, fecha_extraccion, imagenes, fuente
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                cursor.execute(insert_query, (
                    titulo,
                    fecha,
                    resumen,
                    contenido,
                    categoria,
                    autor,
                    tags,  # Usar tags (no keywords)
                    url,
                    datetime.now(),
                    imagenes,
                    source_name
                ))
                
                inserted_count += 1
                
                # Hacer commit después de cada inserción exitosa para evitar problemas de transacción
                conn.commit()
                
            except Exception as e:
                # Si hay error, hacer rollback y continuar
                error_count += 1
                try:
                    conn.rollback()
                except:
                    pass  # Si el rollback falla, continuar de todas formas
                
                if error_count <= 5:  # Log solo los primeros 5 errores
                    print(f"[ERROR] Error insertando noticia {idx}: {e}")
                    if hasattr(e, 'pgcode'):
                        print(f"[ERROR] Código PostgreSQL: {e.pgcode}")
                
                # Continuar con la siguiente noticia
                continue
        
        print(f"[DEBUG] Inserción completada: {inserted_count} insertados, {skipped_no_url} sin URL, {skipped_duplicate} duplicados (por URL), {error_count} errores")
        print(f"[DEBUG] ✅ El único filtro de duplicados es la URL. Todas las noticias con URL única se insertan.")
        
        # Si no se insertó nada, dar más información
        if inserted_count == 0:
            print(f"[DEBUG] ⚠️  No se insertaron noticias. Razones:")
            print(f"[DEBUG]   - Sin URL: {skipped_no_url}")
            print(f"[DEBUG]   - Duplicados: {skipped_duplicate}")
            print(f"[DEBUG]   - Errores: {error_count}")
            print(f"[DEBUG]   - Total procesados: {len(news_data)}")
            
            # Mostrar muestra de URLs para verificar duplicados
            if skipped_duplicate > 0 and len(news_data) > 0:
                print(f"[DEBUG]   - Muestra de URLs (primeras 3):")
                for i, article in enumerate(news_data[:3]):
                    url = article.get('url') or article.get('link') or article.get('href')
                    print(f"[DEBUG]     {i+1}. {url}")
            
        return inserted_count
        
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        print(f"[ERROR] Error general insertando en base de datos: {str(e)}")
        raise Exception(f"Error insertando en base de datos: {str(e)}")
    finally:
        put_conn(conn)


def load_news_from_file(file_path: str) -> List[Dict]:
    """
    Carga noticias desde un archivo CSV o JSON
    """
    if not os.path.exists(file_path):
        return []
    
    news_data = []
    
    try:
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                news_data = json.load(f)
        elif file_path.endswith('.csv'):
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                news_data = list(reader)
    except Exception as e:
        print(f"Error leyendo archivo {file_path}: {e}")
        return []
    
    return news_data


def run_scraper(source_key: str, date_filter: Optional[str] = None, date_start: Optional[str] = None, date_end: Optional[str] = None, limit: Optional[int] = None, categoria: Optional[str] = None) -> Dict:
    """
    Ejecuta un scraper específico e inserta los datos en la tabla 'noticias'
    Retorna diccionario con resultados
    """
    if source_key not in SOURCE_MAPPING:
        raise ValueError(f"Fuente desconocida: {source_key}")
    
    source_info = SOURCE_MAPPING[source_key]
    
    try:
        # Los mocks ya están configurados en setup_dependency_mocks()
        # Importar módulo dinámicamente
        import importlib
        print(f"[DEBUG] Importando módulo: {source_info['module']}")
        try:
            scraper_module = importlib.import_module(source_info["module"])
            print(f"[DEBUG] Módulo importado exitosamente: {scraper_module}")
        except ImportError as import_err:
            print(f"[ERROR] Error importando módulo {source_info['module']}: {import_err}")
            import traceback
            traceback.print_exc()
            raise
        
        # Intentar obtener los datos directamente del scraper antes de guardar archivos
        news_data = []
        inserted_count = 0
        csv_file = None
        json_file = None
        
        # Mapeo de clases de scrapers
        scraper_classes = {
            "pachamama": "PachamamaRadioLocalScraper",
            "punonoticias": "PunonoticiasLocalScraper",
            "losandes": "LosAndesLocalScraper",
            "sinfronteras": "SinFronterasLocalScraper"
            # "test": "TestScraperLocal"  # Deshabilitado
        }
        
        class_name = scraper_classes.get(source_key)
        print(f"[DEBUG] Buscando clase: {class_name} en módulo {scraper_module}")
        print(f"[DEBUG] Atributos del módulo: {dir(scraper_module)}")
        
        if class_name and hasattr(scraper_module, class_name):
            print(f"[DEBUG] Clase {class_name} encontrada en el módulo")
            # Crear instancia del scraper
            scraper_class = getattr(scraper_module, class_name)
            print(f"[DEBUG] Clase obtenida: {scraper_class}")
            
            # Intentar crear el scraper, manejando errores de pandas
            try:
                print(f"[DEBUG] Creando instancia del scraper...")
                scraper = scraper_class()
                print(f"[DEBUG] Instancia creada exitosamente: {scraper}")
            except ImportError as e:
                if 'pandas' in str(e):
                    # Si el error es por pandas, crear un mock antes de importar
                    import types
                    pandas_mock = types.ModuleType('pandas')
                    pandas_mock.__version__ = '2.0.0'
                    
                    class DataFrameMock:
                        def __init__(self, data):
                            self.data = data
                        def to_csv(self, *args, **kwargs):
                            pass
                    
                    pandas_mock.DataFrame = DataFrameMock
                    sys.modules['pandas'] = pandas_mock
                    
                    # Reintentar crear el scraper
                    scraper = scraper_class()
                else:
                    raise
            
            # Ejecutar scraping directamente sin usar main() que requiere pandas
            try:
                print(f"[DEBUG] Intentando obtener datos del scraper {source_key}...")
                print(f"[DEBUG] Métodos del scraper: {[m for m in dir(scraper) if not m.startswith('_')]}")
                
                if hasattr(scraper, 'scrape_news'):
                    print(f"[DEBUG] Método scrape_news encontrado")
                    # Método principal de scraping
                    print(f"[DEBUG] Llamando a scrape_news()...")
                    print(f"[DEBUG] NOTA: Esto puede tardar varios minutos. Los scrapers procesan muchos artículos.")
                    
                    try:
                        # Para hacer pruebas más rápidas, intentar limitar la cantidad de artículos
                        # Algunos scrapers pueden tener un parámetro para limitar
                        import inspect
                        sig = inspect.signature(scraper.scrape_news)
                        
                        # Si el método acepta un parámetro de límite, usarlo
                        if 'limit' in sig.parameters or 'max_articles' in sig.parameters:
                            print(f"[DEBUG] Scraper acepta parámetro de límite, limitando a 20 artículos para prueba rápida")
                            try:
                                news_data = scraper.scrape_news(limit=20)
                            except TypeError:
                                try:
                                    news_data = scraper.scrape_news(max_articles=20)
                                except:
                                    print(f"[DEBUG] No se pudo usar límite, ejecutando sin límite...")
                                    news_data = scraper.scrape_news()
                        else:
                            # Si no acepta límite, ejecutar normalmente pero puede tardar
                            print(f"[DEBUG] Ejecutando scraping completo (puede tardar varios minutos)...")
                            print(f"[DEBUG] NOTA: El scraper puede tardar varios minutos en completarse...")
                            
                            # Para Los Andes, puede aceptar max_workers como parámetro
                            if source_key == "losandes":
                                print(f"[DEBUG] Scraper de Los Andes detectado, usando max_workers=3 para evitar sobrecarga...")
                                try:
                                    news_data = scraper.scrape_news(max_workers=3)
                                except TypeError:
                                    # Si no acepta max_workers, ejecutar sin parámetros
                                    print(f"[DEBUG] Scraper no acepta max_workers, ejecutando sin parámetros...")
                                    news_data = scraper.scrape_news()
                            elif source_key == "test":
                                # Scraper de prueba - ejecutar directamente
                                print(f"[DEBUG] Scraper de prueba detectado, ejecutando sin parámetros...")
                                news_data = scraper.scrape_news()
                                print(f"[DEBUG] Scraper de prueba retornó: {type(news_data)}, longitud: {len(news_data) if news_data else 0}")
                            else:
                                news_data = scraper.scrape_news()
                            
                            # Limitar resultados después si hay muchos (solo para pruebas)
                            if news_data and len(news_data) > 100:
                                print(f"[DEBUG] Se obtuvieron {len(news_data)} artículos, limitando a 100 para inserción")
                                news_data = news_data[:100]
                        
                        print(f"[DEBUG] scrape_news() retornó {len(news_data) if news_data else 0} artículos")
                        if news_data:
                            print(f"[DEBUG] Tipo de news_data: {type(news_data)}")
                            if isinstance(news_data, list) and len(news_data) > 0:
                                print(f"[DEBUG] Primer artículo tiene keys: {list(news_data[0].keys()) if isinstance(news_data[0], dict) else 'No es dict'}")
                                # Verificar si tiene URL
                                first_url = news_data[0].get('url') or news_data[0].get('link') or news_data[0].get('href')
                                print(f"[DEBUG] Primer artículo URL: {first_url}")
                        else:
                            print(f"[DEBUG] ⚠️  news_data está vacío o es None después de scrape_news()")
                            # Verificar si el scraper tiene all_news como atributo
                            if hasattr(scraper, 'all_news'):
                                print(f"[DEBUG] Scraper tiene atributo all_news con {len(scraper.all_news) if scraper.all_news else 0} elementos")
                                if scraper.all_news:
                                    news_data = scraper.all_news
                                    print(f"[DEBUG] Usando all_news del scraper: {len(news_data)} artículos")
                            # También verificar otros atributos comunes
                            if not news_data:
                                if hasattr(scraper, 'articles_data'):
                                    print(f"[DEBUG] Verificando articles_data: {len(scraper.articles_data) if scraper.articles_data else 0} elementos")
                                    if scraper.articles_data:
                                        news_data = scraper.articles_data
                                        print(f"[DEBUG] Usando articles_data del scraper: {len(news_data)} artículos")
                                if not news_data and hasattr(scraper, 'news_data'):
                                    print(f"[DEBUG] Verificando news_data: {len(scraper.news_data) if scraper.news_data else 0} elementos")
                                    if scraper.news_data:
                                        news_data = scraper.news_data
                                        print(f"[DEBUG] Usando news_data del scraper: {len(news_data)} artículos")
                    except Exception as scrape_method_error:
                        import traceback
                        error_trace = traceback.format_exc()
                        print(f"[ERROR] Error al llamar scrape_news(): {scrape_method_error}")
                        print(f"[ERROR] Traceback: {error_trace}")
                        news_data = []
                elif hasattr(scraper, 'scrape_all_news'):
                    # Método alternativo
                    print(f"[DEBUG] Llamando a scrape_all_news()...")
                    news_data = scraper.scrape_all_news()
                    print(f"[DEBUG] scrape_all_news() retornó {len(news_data) if news_data else 0} artículos")
                else:
                    # Intentar obtener datos de atributos después de inicializar
                    # Primero intentar ejecutar métodos que no requieren pandas
                    if hasattr(scraper, 'get_all_article_links'):
                        print(f"[DEBUG] Llamando a get_all_article_links()...")
                        links = scraper.get_all_article_links()
                        print(f"[DEBUG] get_all_article_links() retornó {len(links) if links else 0} enlaces")
                        if links and hasattr(scraper, 'scrape_article'):
                            news_data = []
                            for link in list(links)[:100]:  # Limitar para no sobrecargar
                                article = scraper.scrape_article(link)
                                if article:
                                    news_data.append(article)
                            print(f"[DEBUG] Se obtuvieron {len(news_data)} artículos mediante scrape_article()")
                    
                    # Si aún no hay datos, buscar en atributos
                    if not news_data:
                        print(f"[DEBUG] Buscando datos en atributos del scraper...")
                        if hasattr(scraper, 'articles_data'):
                            news_data = scraper.articles_data
                            print(f"[DEBUG] articles_data tiene {len(news_data) if news_data else 0} artículos")
                        elif hasattr(scraper, 'all_news'):
                            news_data = scraper.all_news
                            print(f"[DEBUG] all_news tiene {len(news_data) if news_data else 0} artículos")
                        elif hasattr(scraper, 'news_data'):
                            news_data = scraper.news_data
                            print(f"[DEBUG] news_data tiene {len(news_data) if news_data else 0} artículos")
                
                # Verificar si news_data es válido
                if news_data:
                    # Asegurar que es una lista
                    if not isinstance(news_data, list):
                        print(f"[DEBUG] news_data no es una lista, es {type(news_data)}")
                        news_data = []
                    else:
                        # Filtrar elementos None o vacíos
                        news_data = [item for item in news_data if item]
                        print(f"[DEBUG] Después de filtrar, quedan {len(news_data)} artículos válidos")
                        
                        # Mostrar muestra de los primeros artículos para debug
                        if news_data and len(news_data) > 0:
                            sample = news_data[0]
                            print(f"[DEBUG] Muestra del primer artículo:")
                            print(f"[DEBUG]   - Título: {sample.get('titulo', sample.get('title', 'N/A'))[:50]}")
                            print(f"[DEBUG]   - URL: {sample.get('url', sample.get('link', 'N/A'))}")
                            print(f"[DEBUG]   - Tiene contenido: {bool(sample.get('contenido', sample.get('content', '')))}")
                
                # Si aún no hay datos, intentar leer archivos JSON existentes más recientes
                if not news_data:
                    print(f"[DEBUG] No se obtuvieron datos directamente, buscando archivos JSON...")
                    # Buscar archivos JSON más recientes en la carpeta de datos
                    data_folder = getattr(scraper, 'data_folder', f"data/{source_key}")
                    print(f"[DEBUG] Buscando en carpeta: {data_folder}")
                    if os.path.exists(data_folder):
                        json_files = [f for f in os.listdir(data_folder) if f.endswith('.json')]
                        print(f"[DEBUG] Se encontraron {len(json_files)} archivos JSON")
                        if json_files:
                            # Ordenar por fecha de modificación (más reciente primero)
                            json_files.sort(key=lambda x: os.path.getmtime(os.path.join(data_folder, x)), reverse=True)
                            latest_json = os.path.join(data_folder, json_files[0])
                            print(f"[DEBUG] Cargando archivo más reciente: {latest_json}")
                            news_data = load_news_from_file(latest_json)
                            if news_data:
                                json_file = latest_json
                                print(f"[DEBUG] Se cargaron {len(news_data)} artículos desde archivo JSON")
                            else:
                                print(f"[DEBUG] El archivo JSON está vacío o no se pudo leer")
                    else:
                        print(f"[DEBUG] La carpeta de datos no existe: {data_folder}")
                                
            except Exception as scrape_error:
                # Si hay error al obtener datos directamente, intentar con archivos
                import traceback
                error_trace = traceback.format_exc()
                print(f"[ERROR] Error obteniendo datos directamente: {scrape_error}")
                print(f"[ERROR] Traceback completo:")
                print(error_trace)
                
                # Intentar obtener datos de atributos del scraper incluso después del error
                if not news_data:
                    print(f"[DEBUG] Intentando obtener datos de atributos del scraper después del error...")
                    if hasattr(scraper, 'all_news') and scraper.all_news:
                        news_data = scraper.all_news
                        print(f"[DEBUG] Se obtuvieron {len(news_data)} artículos de all_news después del error")
                    elif hasattr(scraper, 'articles_data') and scraper.articles_data:
                        news_data = scraper.articles_data
                        print(f"[DEBUG] Se obtuvieron {len(news_data)} artículos de articles_data después del error")
                    elif hasattr(scraper, 'news_data') and scraper.news_data:
                        news_data = scraper.news_data
                        print(f"[DEBUG] Se obtuvieron {len(news_data)} artículos de news_data después del error")
                
                # Buscar archivos JSON más recientes
                if not news_data:
                    data_folder = getattr(scraper, 'data_folder', f"data/{source_key}")
                    print(f"[DEBUG] Buscando archivos JSON en: {data_folder}")
                    if os.path.exists(data_folder):
                        json_files = [f for f in os.listdir(data_folder) if f.endswith('.json')]
                        if json_files:
                            json_files.sort(key=lambda x: os.path.getmtime(os.path.join(data_folder, x)), reverse=True)
                            latest_json = os.path.join(data_folder, json_files[0])
                            print(f"[DEBUG] Cargando archivo JSON más reciente: {latest_json}")
                            news_data = load_news_from_file(latest_json)
                            if news_data:
                                json_file = latest_json
                                print(f"[DEBUG] Se cargaron {len(news_data)} artículos desde archivo JSON después del error")
                            else:
                                print(f"[DEBUG] El archivo JSON está vacío o no se pudo leer")
                        else:
                            print(f"[DEBUG] No se encontraron archivos JSON en {data_folder}")
                    else:
                        print(f"[DEBUG] La carpeta de datos no existe: {data_folder}")
        else:
            # Si no hay clase, no podemos hacer scraping sin pandas
            raise Exception(f"No se encontró la clase del scraper para {source_key}")
        
        # NOTA: El filtro de fecha se usa para LIMITAR qué se scrapea del sitio web,
        # no para filtrar después de obtener los datos. Si un artículo no coincide con el filtro,
        # significa que NO está en la base de datos y DEBE ser insertado.
        # Por lo tanto, NO filtramos aquí - todos los artículos obtenidos se insertan.
        # El filtro de fecha solo afecta qué artículos el scraper busca en el sitio web.
        
        # Filtrar por categoría si se especificó
        if news_data and len(news_data) > 0 and categoria:
            print(f"[DEBUG] Filtrando artículos por categoría: {categoria}...")
            original_count = len(news_data)
            filtered_data = []
            
            for article in news_data:
                article_categoria = article.get('categoria') or article.get('category')
                if article_categoria and categoria.lower() in article_categoria.lower():
                    filtered_data.append(article)
            
            news_data = filtered_data
            print(f"[DEBUG] Después del filtro de categoría: {len(news_data)} artículos (de {original_count} originales)")
        
        # Aplicar límite si se especificó
        if news_data and len(news_data) > 0 and limit:
            print(f"[DEBUG] Aplicando límite de {limit} artículos...")
            original_count = len(news_data)
            news_data = news_data[:limit]
            print(f"[DEBUG] Después del límite: {len(news_data)} artículos (de {original_count} originales)")
        
        # Insertar en la tabla 'noticias'
        print(f"[DEBUG] Total de artículos obtenidos: {len(news_data) if news_data else 0}")
        if news_data and len(news_data) > 0:
            print(f"[DEBUG] Insertando {len(news_data)} artículos en la base de datos...")
            try:
                inserted_count = insert_news_to_database(news_data, source_info["name"])
                print(f"[DEBUG] Se insertaron {inserted_count} artículos en la base de datos")
            except Exception as insert_error:
                import traceback
                error_trace = traceback.format_exc()
                print(f"[ERROR] Error al insertar en base de datos: {insert_error}")
                print(f"[ERROR] Traceback: {error_trace}")
                return {
                    "source": source_info["name"],
                    "status": "error",
                    "message": f"Error al insertar en base de datos: {str(insert_error)}",
                    "error": str(insert_error),
                    "traceback": error_trace,
                    "inserted_count": 0
                }
        else:
            print(f"[DEBUG] ⚠️  No hay datos para insertar")
            print(f"[DEBUG] news_data es: {type(news_data)} - {news_data}")
            
            # Intentar una última vez obtener datos de atributos del scraper
            if not news_data and 'scraper' in locals():
                print(f"[DEBUG] Último intento: verificando atributos del scraper...")
                if hasattr(scraper, 'all_news') and scraper.all_news:
                    news_data = scraper.all_news
                    print(f"[DEBUG] ✅ Se encontraron {len(news_data)} artículos en all_news")
                elif hasattr(scraper, 'articles_data') and scraper.articles_data:
                    news_data = scraper.articles_data
                    print(f"[DEBUG] ✅ Se encontraron {len(news_data)} artículos en articles_data")
                elif hasattr(scraper, 'news_data') and scraper.news_data:
                    news_data = scraper.news_data
                    print(f"[DEBUG] ✅ Se encontraron {len(news_data)} artículos en news_data")
            
            if not news_data:
                return {
                    "source": source_info["name"],
                    "status": "error",
                    "message": f"No se obtuvieron datos del scraper de {source_info['name']}. El scraper puede no haber encontrado artículos o puede haber un problema con el método scrape_news(). Revisa los logs del servidor para más detalles.",
                    "inserted_count": 0
                }
        
        return {
            "source": source_info["name"],
            "status": "success",
            "csv_file": csv_file if csv_file else None,
            "json_file": json_file if json_file else None,
            "inserted_count": inserted_count,
            "message": f"Scraping de {source_info['name']} completado. {inserted_count} noticia(s) insertada(s) en la tabla 'noticias'"
        }
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            "source": source_info["name"],
            "status": "error",
            "message": f"Error en scraping de {source_info['name']}: {str(e)}",
            "error": str(e),
            "traceback": error_trace
        }


def run_scraping_job(job_id: str, config: Dict):
    """
    Ejecuta un trabajo de scraping en background
    """
    scraping_status[job_id] = {
        "status": "running",
        "progress": 0.0,
        "current_source": None,
        "results": [],
        "logs": [],
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Determinar fuentes a procesar
        sources_to_process = []
        
        if config["type"] == "complete":
            sources_to_process = list(SOURCE_MAPPING.keys())
        elif config["type"] == "selected" and config.get("sources"):
            sources_to_process = config["sources"]
        elif config["type"] == "single" and config.get("source"):
            sources_to_process = [config["source"]]
        elif config["type"] in ["date", "today", "yesterday", "week", "month", "dateRange"]:
            # Para scraping por fecha, procesar todas las fuentes
            # (la lógica de filtrado por fecha se haría en el scraper)
            sources_to_process = list(SOURCE_MAPPING.keys())
        else:
            scraping_status[job_id]["status"] = "error"
            scraping_status[job_id]["logs"].append("❌ Error: Configuración inválida")
            return
        
        total_sources = len(sources_to_process)
        scraping_status[job_id]["logs"].append(f"🚀 Iniciando scraping de {total_sources} fuente(s)...")
        
        # Procesar cada fuente
        for idx, source_key in enumerate(sources_to_process):
            if source_key not in SOURCE_MAPPING:
                continue
            
            source_name = SOURCE_MAPPING[source_key]["name"]
            scraping_status[job_id]["current_source"] = source_name
            scraping_status[job_id]["logs"].append(f"\n🕷️  Procesando: {source_name}")
            
            # Actualizar progreso
            progress = (idx / total_sources) * 100
            scraping_status[job_id]["progress"] = progress
            
            # Ejecutar scraper con filtros de fecha si aplican
            try:
                scraping_status[job_id]["logs"].append(f"   🔄 Iniciando scraper para {source_name}...")
                
                # Pasar parámetros de fecha si están configurados
                date_filter = config.get("date")
                date_start = config.get("date_start")
                date_end = config.get("date_end")
                limit = config.get("limit")
                categoria = config.get("categoria")
                
                # Log de filtros aplicados
                filter_logs = []
                if date_filter:
                    filter_logs.append(f"📅 Fecha: {date_filter}")
                elif date_start and date_end:
                    filter_logs.append(f"📅 Rango: {date_start} a {date_end}")
                if limit:
                    filter_logs.append(f"🔢 Límite: {limit} noticias")
                if categoria:
                    filter_logs.append(f"📂 Categoría: {categoria}")
                
                if filter_logs:
                    scraping_status[job_id]["logs"].append(f"   🔍 Filtros: {', '.join(filter_logs)}")
                
                result = run_scraper(source_key, date_filter=date_filter, date_start=date_start, date_end=date_end, limit=limit, categoria=categoria)
                scraping_status[job_id]["results"].append(result)
                
                # Agregar log según resultado
                if result["status"] == "success":
                    inserted = result.get("inserted_count", 0)
                    scraping_status[job_id]["logs"].append(f"   ✅ {result.get('message', 'Completado')}")
                    if inserted > 0:
                        scraping_status[job_id]["logs"].append(f"   📊 {inserted} noticia(s) insertada(s) en la tabla 'noticias'")
                    else:
                        scraping_status[job_id]["logs"].append(f"   ⚠️  Scraping completado pero no se insertaron noticias (puede ser que ya existan o no se obtuvieron datos)")
                else:
                    scraping_status[job_id]["logs"].append(f"   ❌ {result.get('message', 'Error')}")
                    if result.get("error"):
                        scraping_status[job_id]["logs"].append(f"   🔍 Error: {result['error']}")
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                scraping_status[job_id]["logs"].append(f"   ❌ Excepción al ejecutar scraper: {str(e)}")
                scraping_status[job_id]["logs"].append(f"   📋 Traceback: {error_trace[:500]}...")  # Limitar tamaño
                result = {
                    "source": source_name,
                    "status": "error",
                    "message": f"Excepción: {str(e)}",
                    "error": str(e),
                    "inserted_count": 0
                }
                scraping_status[job_id]["results"].append(result)
        
        # Completar
        scraping_status[job_id]["status"] = "completed"
        scraping_status[job_id]["progress"] = 100.0
        scraping_status[job_id]["current_source"] = None
        scraping_status[job_id]["logs"].append(f"\n🎉 Scraping completado exitosamente!")
        
        # Contar noticias procesadas
        total_sources = sum(1 for r in scraping_status[job_id]["results"] if r["status"] == "success")
        total_news = sum(r.get("inserted_count", 0) for r in scraping_status[job_id]["results"])
        scraping_status[job_id]["logs"].append(f"📊 Total: {total_sources} fuente(s) procesada(s)")
        scraping_status[job_id]["logs"].append(f"📰 Total: {total_news} noticia(s) insertada(s) en la tabla 'noticias'")
        
    except Exception as e:
        scraping_status[job_id]["status"] = "error"
        scraping_status[job_id]["logs"].append(f"❌ Error durante el scraping: {str(e)}")


@router.post("/scrapers/run", response_model=ScrapingResponse)
async def run_scraping(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks
):
    """
    Inicia un trabajo de scraping
    """
    # Generar ID único para el trabajo
    job_id = f"scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Validar configuración
    if request.type == "selected" and (not request.sources or len(request.sources) == 0):
        raise HTTPException(status_code=400, detail="Debes seleccionar al menos una fuente")
    
    if request.type == "single" and not request.source:
        raise HTTPException(status_code=400, detail="Debes seleccionar una fuente")
    
    if request.type == "date" and not request.date:
        raise HTTPException(status_code=400, detail="Debes seleccionar una fecha")
    
    if request.type == "dateRange" and (not request.date_start or not request.date_end):
        raise HTTPException(status_code=400, detail="Debes seleccionar ambas fechas del rango")
    
    # Preparar configuración
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    config = {
        "type": request.type,
        "sources": request.sources,
        "source": request.source,
        "date": request.date if request.type == "date" else (
            today if request.type == "today" else (
                yesterday if request.type == "yesterday" else None
            )
        ),
        "date_start": request.date_start if request.type in ["week", "month", "dateRange"] else (
            week_ago if request.type == "week" else (
                month_ago if request.type == "month" else None
            )
        ),
        "date_end": request.date_end if request.type in ["week", "month", "dateRange"] else (
            today if request.type in ["week", "month"] else None
        ),
        "limit": request.limit,
        "categoria": request.categoria
    }
    
    # Si hay filtro de fuente en tipos basados en fecha, ajustar configuración
    if request.source and request.type in ["date", "today", "yesterday", "week", "month", "dateRange"]:
        # Cambiar a tipo 'single' con la fuente especificada
        config["type"] = "single"
        # Mantener los filtros de fecha
    
    # Ejecutar en background
    background_tasks.add_task(run_scraping_job, job_id, config)
    
    return ScrapingResponse(
        job_id=job_id,
        status="running",
        message="Scraping iniciado",
        timestamp=datetime.now().isoformat()
    )


@router.get("/scrapers/status/{job_id}", response_model=ScrapingStatusResponse)
async def get_scraping_status(job_id: str):
    """
    Obtiene el estado de un trabajo de scraping
    """
    if job_id not in scraping_status:
        raise HTTPException(status_code=404, detail="Trabajo de scraping no encontrado")
    
    status = scraping_status[job_id]
    
    return ScrapingStatusResponse(
        job_id=job_id,
        status=status["status"],
        progress=status["progress"],
        current_source=status.get("current_source"),
        results=status["results"],
        logs=status["logs"],
        timestamp=status["timestamp"]
    )


@router.get("/scrapers/sources")
async def get_available_sources():
    """
    Obtiene la lista de fuentes disponibles
    """
    return {
        "sources": [
            {
                "id": key,
                "name": info["name"],
                "module": info["module"]
            }
            for key, info in SOURCE_MAPPING.items()
        ]
    }


@router.post("/scrapers/run-source/{source_id}")
async def run_single_source(
    source_id: str,
    background_tasks: BackgroundTasks
):
    """
    Ejecuta scraping de una fuente específica
    """
    if source_id not in SOURCE_MAPPING:
        raise HTTPException(status_code=404, detail="Fuente no encontrada")
    
    job_id = f"scraping_{source_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    config = {
        "type": "single",
        "source": source_id
    }
    
    background_tasks.add_task(run_scraping_job, job_id, config)
    
    return ScrapingResponse(
        job_id=job_id,
        status="running",
        message=f"Scraping de {SOURCE_MAPPING[source_id]['name']} iniciado",
        timestamp=datetime.now().isoformat()
    )


@router.delete("/scrapers/status/{job_id}")
async def clear_scraping_status(job_id: str):
    """
    Limpia el estado de un trabajo de scraping completado
    """
    if job_id in scraping_status:
        # Solo permitir limpiar trabajos completados o con error
        if scraping_status[job_id]["status"] in ["completed", "error"]:
            del scraping_status[job_id]
            return {"message": "Estado limpiado exitosamente"}
        else:
            raise HTTPException(status_code=400, detail="No se puede limpiar un trabajo en progreso")
    else:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")


# Estado global de migración
migration_status: Dict[str, Dict] = {}


def run_migration_job(job_id: str):
    """
    Ejecuta la migración de noticias a noticias_limpia en background
    Sin necesidad de pandas - todo se hace con SQL y Python puro
    """
    from datetime import datetime as dt
    from urllib.parse import urlparse
    
    migration_status[job_id] = {
        "status": "running",
        "progress": 0.0,
        "current_step": None,
        "logs": [],
        "timestamp": datetime.now().isoformat(),
        "results": {}
    }
    
    # Funciones auxiliares para normalización (sin pandas)
    def extract_keywords(titulo):
        """Extraer palabras clave del título"""
        if not titulo:
            return ''
        import re
        stop_words = {'de', 'la', 'el', 'en', 'y', 'a', 'los', 'las', 'del', 'se', 'con', 
                     'por', 'para', 'su', 'al', 'lo', 'un', 'una', 'unos', 'unas', 'es', 'son',
                     'que', 'como', 'más', 'pero', 'o', 'sin', 'sobre', 'bajo', 'entre'}
        palabras = re.findall(r'\b[a-zA-Záéíóúñ]{4,}\b', str(titulo).lower())
        keywords = [p for p in palabras if p not in stop_words]
        return ', '.join(keywords[:5])
    
    def categorize_article(titulo, contenido):
        """Categorizar artículo basado en título y contenido"""
        if not titulo:
            return 'Otros'
        text = f"{titulo} {contenido or ''}".lower()
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
    
    def estandarizar_fuente(fuente):
        """Estandarizar nombres de fuentes"""
        if not fuente:
            return 'Desconocida'
        fuente_lower = str(fuente).lower()
        if 'pachamama' in fuente_lower:
            return 'Pachamama Radio'
        elif 'los_andes' in fuente_lower or 'andes' in fuente_lower:
            return 'Los Andes'
        elif 'puno' in fuente_lower and 'noticias' in fuente_lower:
            return 'Puno Noticias'
        elif 'sin fronteras' in fuente_lower:
            return 'Sin Fronteras'
        else:
            return str(fuente).title()
    
    def identificar_tipo_contenido(titulo, cantidad_imagenes):
        """Identificar tipo de contenido"""
        titulo_lower = str(titulo).lower()
        if any(word in titulo_lower for word in ['?', '¿cómo', 'guía', 'práctica']):
            return 'Guía/Instructivo'
        elif any(word in titulo_lower for word in ['anuncia', 'nuevo', 'lanzamiento']):
            return 'Anuncio'
        elif any(word in titulo_lower for word in ['alerta', 'advierten', 'peligro']):
            return 'Alerta'
        elif any(word in titulo_lower for word in ['investigación', 'estudio', 'descubrimiento']):
            return 'Investigación'
        elif cantidad_imagenes > 1:
            return 'Galería'
        else:
            return 'Noticia'
    
    try:
        # Paso 1: Crear tabla si no existe
        migration_status[job_id]["current_step"] = "setup"
        migration_status[job_id]["progress"] = 5.0
        migration_status[job_id]["logs"].append("🔧 Configurando tabla 'noticias_limpia'...")
        
        conn = get_conn()
        if not conn:
            raise Exception("No se pudo obtener conexión a la base de datos")
        
        cursor = conn.cursor()
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS noticias_limpia (
            id SERIAL PRIMARY KEY,
            titulo TEXT NOT NULL,
            fecha DATE,
            hora TIME,
            anio FLOAT,
            mes FLOAT,
            dia FLOAT,
            dia_semana VARCHAR(20),
            resumen TEXT,
            contenido TEXT,
            categoria VARCHAR(100),
            autor VARCHAR(255),
            keywords TEXT,
            url TEXT NOT NULL UNIQUE,
            dominio VARCHAR(255),
            fecha_extraccion TIMESTAMP,
            imagen_principal TEXT,
            cantidad_imagenes INTEGER,
            tiene_imagenes BOOLEAN,
            fuente VARCHAR(100),
            longitud_titulo INTEGER,
            longitud_resumen FLOAT,
            tipo_contenido VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
        migration_status[job_id]["logs"].append("✅ Tabla 'noticias_limpia' creada/verificada")
        
        # Contar registros existentes
        cursor.execute("SELECT COUNT(*) FROM noticias_limpia")
        count_before = cursor.fetchone()[0]
        migration_status[job_id]["logs"].append(f"📊 Registros existentes: {count_before}")
        
        # Paso 2: Exportar y procesar datos de noticias
        migration_status[job_id]["current_step"] = "export"
        migration_status[job_id]["progress"] = 10.0
        migration_status[job_id]["logs"].append("📤 Paso 2: Exportando y procesando datos de 'noticias'...")
        
        cursor.execute("""
            SELECT 
                id, titulo, fecha, resumen, contenido, categoria, autor, 
                tags, url, fecha_extraccion, imagenes, fuente, created_at
            FROM noticias 
            ORDER BY fecha_extraccion DESC
        """)
        
        data = cursor.fetchall()
        migration_status[job_id]["logs"].append(f"✅ Exportación completada: {len(data)} registros")
        migration_status[job_id]["progress"] = 30.0
        
        # Paso 3: Normalizar y preparar datos
        migration_status[job_id]["current_step"] = "normalize"
        migration_status[job_id]["logs"].append("🔄 Paso 3: Normalizando datos...")
        
        data_tuples = []
        for row in data:
            (id_val, titulo, fecha, resumen, contenido, categoria, autor, 
             tags, url, fecha_extraccion, imagenes, fuente, created_at) = row
            
            # Procesar fecha
            fecha_val = None
            hora_val = None
            anio = None
            mes = None
            dia = None
            dia_semana = None
            
            if fecha:
                try:
                    if isinstance(fecha, str):
                        fecha_dt = dt.strptime(fecha.split()[0], '%Y-%m-%d')
                    else:
                        fecha_dt = fecha
                    fecha_val = fecha_dt.date()
                    anio = float(fecha_dt.year)
                    mes = float(fecha_dt.month)
                    dia = float(fecha_dt.day)
                    dia_semana = fecha_dt.strftime('%A')
                except:
                    pass
            
            # Procesar imágenes
            imagen_principal = None
            cantidad_imagenes = 0
            tiene_imagenes = False
            if imagenes:
                urls = [url.strip() for url in str(imagenes).split(';') if url.strip()]
                cantidad_imagenes = len(urls)
                tiene_imagenes = cantidad_imagenes > 0
                imagen_principal = urls[0] if urls else None
            
            # Limpiar URL y extraer dominio
            url_limpia = url.split('#')[0].strip() if url else ''
            dominio = None
            try:
                parsed = urlparse(url_limpia)
                dominio = parsed.netloc
            except:
                pass
            
            # Normalizar datos
            categoria_auto = categoria or categorize_article(titulo or '', contenido or '')
            keywords_str = tags or extract_keywords(titulo)
            fuente_estandarizada = estandarizar_fuente(fuente)
            longitud_titulo = len(titulo) if titulo else 0
            longitud_resumen = float(len(resumen)) if resumen else 0.0
            tipo_contenido = identificar_tipo_contenido(titulo or '', cantidad_imagenes)
            
            # Crear resumen si está vacío
            resumen_final = resumen if resumen else (f"{titulo}. Información completa disponible en el contenido principal." if titulo else '')
            
            data_tuples.append((
                str(titulo or ''),
                fecha_val,
                hora_val,
                anio,
                mes,
                dia,
                dia_semana,
                resumen_final,
                str(contenido or ''),
                categoria_auto,
                str(autor or ''),
                keywords_str,
                url_limpia,
                dominio,
                fecha_extraccion,
                imagen_principal,
                cantidad_imagenes,
                tiene_imagenes,
                fuente_estandarizada,
                longitud_titulo,
                longitud_resumen,
                tipo_contenido,
                created_at
            ))
        
        migration_status[job_id]["logs"].append(f"✅ Normalización completada: {len(data_tuples)} registros")
        migration_status[job_id]["progress"] = 60.0
        
        # Paso 4: Cargar a noticias_limpia
        migration_status[job_id]["current_step"] = "load"
        migration_status[job_id]["logs"].append("📥 Paso 4: Cargando datos a 'noticias_limpia'...")
        
        # Preparar query de inserción
        insert_query = """
        INSERT INTO noticias_limpia (
            titulo, fecha, hora, anio, mes, dia, dia_semana, resumen, contenido,
            categoria, autor, keywords, url, dominio, fecha_extraccion, imagen_principal,
            cantidad_imagenes, tiene_imagenes, fuente, longitud_titulo, longitud_resumen,
            tipo_contenido, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (url) DO NOTHING
        """
        
        # Insertar en lotes
        batch_size = 100
        total_processed = 0
        total_inserted = 0
        total_skipped = 0
        
        for i in range(0, len(data_tuples), batch_size):
            batch = data_tuples[i:i + batch_size]
            try:
                cursor.executemany(insert_query, batch)
                conn.commit()
                inserted_in_batch = cursor.rowcount
                total_inserted += inserted_in_batch
                total_skipped += len(batch) - inserted_in_batch
                total_processed += len(batch)
                progress = 60 + (total_processed / len(data_tuples)) * 35
                migration_status[job_id]["progress"] = min(progress, 95.0)
                migration_status[job_id]["logs"].append(f"📝 Procesados {total_processed}/{len(data_tuples)} registros... (Insertados: {total_inserted}, Omitidos: {total_skipped})")
            except Exception as e:
                migration_status[job_id]["logs"].append(f"⚠️  Error en lote {i//batch_size + 1}: {e}")
                conn.rollback()
                # Intentar insertar uno por uno
                for record in batch:
                    try:
                        cursor.execute(insert_query, record)
                        conn.commit()
                        total_inserted += 1
                    except:
                        total_skipped += 1
                        conn.rollback()
        
        # Verificar resultados
        cursor.execute("SELECT COUNT(*) FROM noticias_limpia")
        total_count = cursor.fetchone()[0]
        new_records = total_count - count_before
        
        cursor.execute("""
            SELECT fuente, COUNT(*) as cantidad 
            FROM noticias_limpia 
            GROUP BY fuente 
            ORDER BY cantidad DESC
        """)
        fuentes = cursor.fetchall()
        
        migration_status[job_id]["results"] = {
            "count_before": int(count_before),
            "new_records": int(new_records),
            "total_skipped": int(total_skipped),
            "total_count": int(total_count),
            "fuentes": {fuente: int(cantidad) for fuente, cantidad in fuentes}
        }
        
        migration_status[job_id]["logs"].append(f"\n✅ Migración completada:")
        migration_status[job_id]["logs"].append(f"   📊 Registros antes: {count_before}")
        migration_status[job_id]["logs"].append(f"   ➕ Registros nuevos: {new_records}")
        migration_status[job_id]["logs"].append(f"   ⏭️  Registros omitidos (duplicados): {total_skipped}")
        migration_status[job_id]["logs"].append(f"   📊 Total en noticias_limpia: {total_count}")
        
        cursor.close()
        put_conn(conn)
        
        migration_status[job_id]["status"] = "completed"
        migration_status[job_id]["progress"] = 100.0
        migration_status[job_id]["current_step"] = None
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        migration_status[job_id]["status"] = "error"
        migration_status[job_id]["logs"].append(f"❌ Error: {str(e)}")
        migration_status[job_id]["logs"].append(f"📋 Traceback: {error_trace[:500]}")


@router.post("/scrapers/migrate")
async def start_migration(background_tasks: BackgroundTasks):
    """
    Inicia la migración de noticias a noticias_limpia
    """
    job_id = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    background_tasks.add_task(run_migration_job, job_id)
    
    return {
        "job_id": job_id,
        "status": "running",
        "message": "Migración iniciada",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/scrapers/migrate/status/{job_id}")
async def get_migration_status(job_id: str):
    """
    Obtiene el estado de una migración
    """
    if job_id not in migration_status:
        raise HTTPException(status_code=404, detail="Trabajo de migración no encontrado")
    
    status = migration_status[job_id]
    
    return {
        "job_id": job_id,
        "status": status["status"],
        "progress": status["progress"],
        "current_step": status.get("current_step"),
        "logs": status["logs"],
        "results": status.get("results", {}),
        "timestamp": status["timestamp"]
    }

