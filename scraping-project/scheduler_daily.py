import csv
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
import requests  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"


def get_db_connection():
    """Obtiene una conexión a la base de datos"""
    db_host = os.getenv("PGHOST", "postgres")
    db_name = os.getenv("PGDATABASE", "noticias")
    db_user = os.getenv("PGUSER", "postgres")
    db_password = os.getenv("PGPASSWORD", "123456")
    db_port = os.getenv("PGPORT", "5432")
    
    return psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=db_port
    )


def count_news_by_source(source: str) -> int:
    """Cuenta las noticias de una fuente específica"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM noticias WHERE fuente = %s", (source,))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        print(f"[scheduler] Error counting news for {source}: {e}")
        return 0


def count_social_news() -> int:
    """Cuenta las noticias de redes sociales"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM social_news")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        print(f"[scheduler] Error counting social news: {e}")
        return 0


def get_news_by_source(source: str, since_timestamp: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
    """Obtiene noticias de una fuente específica, opcionalmente desde una fecha"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if since_timestamp:
            cursor.execute("""
                SELECT * FROM noticias 
                WHERE fuente = %s AND fecha_extraccion >= %s
                ORDER BY fecha_extraccion DESC
            """, (source, since_timestamp))
        else:
            cursor.execute("""
                SELECT * FROM noticias 
                WHERE fuente = %s
                ORDER BY fecha_extraccion DESC
            """, (source,))
        
        news = cursor.fetchall()
        # Convertir RealDictRow a dict normal
        news_list = [dict(row) for row in news]
        
        cursor.close()
        conn.close()
        return news_list
    except Exception as e:
        print(f"[scheduler] Error getting news for {source}: {e}")
        return []


def get_social_news(since_timestamp: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
    """Obtiene noticias de redes sociales, opcionalmente desde una fecha"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if since_timestamp:
            cursor.execute("""
                SELECT * FROM social_news 
                WHERE created_at >= %s
                ORDER BY created_at DESC
            """, (since_timestamp,))
        else:
            cursor.execute("""
                SELECT * FROM social_news 
                ORDER BY created_at DESC
            """)
        
        news = cursor.fetchall()
        # Convertir RealDictRow a dict normal
        news_list = [dict(row) for row in news]
        
        cursor.close()
        conn.close()
        return news_list
    except Exception as e:
        print(f"[scheduler] Error getting social news: {e}")
        return []


def ensure_data_dir(source_name: str) -> Path:
    """Asegura que exista el directorio de datos para una fuente"""
    # Mapeo de nombres de fuentes a nombres de carpetas existentes
    folder_mapping = {
        "Los Andes": "losandes",
        "Pachamama Radio": "pachamamaradio",
        "Puno Noticias": "punonoticias",
        "Sin Fronteras": "sinfronteras",
        "redes_sociales": "social-news",
        "Redes Sociales": "social-news",
    }
    
    # Usar el mapeo si existe, sino normalizar el nombre
    folder_name = folder_mapping.get(source_name, source_name.lower().replace(" ", "_"))
    source_dir = DATA_DIR / folder_name
    source_dir.mkdir(parents=True, exist_ok=True)
    return source_dir


def export_to_json(data: List[Dict[str, Any]], filepath: Path) -> bool:
    """Exporta datos a JSON"""
    try:
        # Convertir datetime a string para JSON
        def json_serial(obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=json_serial)
        return True
    except Exception as e:
        print(f"[scheduler] Error exporting to JSON {filepath}: {e}")
        return False


def export_to_csv(data: List[Dict[str, Any]], filepath: Path) -> bool:
    """Exporta datos a CSV"""
    try:
        if not data:
            # Crear archivo vacío con encabezados si no hay datos
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([])
            return True
        
        # Obtener todas las claves de todos los registros
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        
        fieldnames = sorted(all_keys)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            for row in data:
                # Convertir datetime a string
                row_copy = {}
                for key, value in row.items():
                    if isinstance(value, datetime.datetime):
                        row_copy[key] = value.isoformat()
                    else:
                        row_copy[key] = value
                writer.writerow(row_copy)
        
        return True
    except Exception as e:
        print(f"[scheduler] Error exporting to CSV {filepath}: {e}")
        return False


def export_source_news(source_name: str, since_timestamp: datetime.datetime) -> Optional[Dict[str, str]]:
    """Exporta noticias de una fuente a JSON y CSV"""
    print(f"[scheduler] Exportando noticias de {source_name}...")
    
    # Obtener noticias nuevas
    news = get_news_by_source(source_name, since_timestamp)
    
    if not news:
        print(f"[scheduler] No hay noticias nuevas de {source_name} para exportar")
        return None
    
    # Crear directorio
    source_dir = ensure_data_dir(source_name)
    
    # Obtener el nombre de la carpeta (ya normalizado por ensure_data_dir)
    folder_name = source_dir.name
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = source_dir / f"{folder_name}_{timestamp}.json"
    csv_file = source_dir / f"{folder_name}_{timestamp}.csv"
    
    # Exportar
    json_success = export_to_json(news, json_file)
    csv_success = export_to_csv(news, csv_file)
    
    if json_success and csv_success:
        print(f"[scheduler] ✅ Exportadas {len(news)} noticias de {source_name}")
        print(f"[scheduler]    JSON: {json_file.name}")
        print(f"[scheduler]    CSV:  {csv_file.name}")
        return {
            "json": str(json_file),
            "csv": str(csv_file),
            "count": len(news)
        }
    else:
        print(f"[scheduler] ❌ Error exportando noticias de {source_name}")
        return None


def export_social_news(since_timestamp: datetime.datetime) -> Optional[Dict[str, str]]:
    """Exporta noticias de redes sociales a JSON y CSV"""
    print(f"[scheduler] Exportando noticias de redes sociales...")
    
    # Obtener noticias nuevas
    news = get_social_news(since_timestamp)
    
    if not news:
        print(f"[scheduler] No hay noticias nuevas de redes sociales para exportar")
        return None
    
    # Crear directorio
    source_dir = ensure_data_dir("Redes Sociales")
    
    # Obtener el nombre de la carpeta (ya normalizado por ensure_data_dir)
    folder_name = source_dir.name
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = source_dir / f"{folder_name}_{timestamp}.json"
    csv_file = source_dir / f"{folder_name}_{timestamp}.csv"
    
    # Exportar
    json_success = export_to_json(news, json_file)
    csv_success = export_to_csv(news, csv_file)
    
    if json_success and csv_success:
        print(f"[scheduler] ✅ Exportadas {len(news)} noticias de redes sociales")
        print(f"[scheduler]    JSON: {json_file.name}")
        print(f"[scheduler]    CSV:  {csv_file.name}")
        return {
            "json": str(json_file),
            "csv": str(csv_file),
            "count": len(news)
        }
    else:
        print(f"[scheduler] ❌ Error exportando noticias de redes sociales")
        return None


def run(cmd: List[str]) -> int:
    print(f"[scheduler] Running: {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, cwd=PROJECT_ROOT, check=False, 
                             capture_output=True, text=True)
        # Mostrar salida de Scrapy si hay errores
        if proc.returncode != 0 and proc.stderr:
            print(f"[scheduler] Error output: {proc.stderr[:500]}")
        return proc.returncode
    except Exception as exc:
        print(f"[scheduler] Error: {exc}")
        return 1


def run_local_scraper(module_name: str, class_name: str) -> int:
    """Ejecuta un scraper local (no Scrapy)"""
    try:
        # Importar el módulo del scraper
        import importlib
        scraper_module = importlib.import_module(f"spiders.{module_name}")
        scraper_class = getattr(scraper_module, class_name)
        
        # Crear instancia y ejecutar
        scraper = scraper_class()
        if hasattr(scraper, 'main'):
            scraper.main()
        elif hasattr(scraper, 'run_complete_scraping'):
            scraper.run_complete_scraping()
        elif hasattr(scraper, 'scrape_news'):
            scraper.scrape_news()
            scraper.save_to_csv()
            scraper.save_to_json()
        else:
            print(f"[scheduler] ERROR: No se encontró método de ejecución en {class_name}")
            return 1
        
        return 0
    except Exception as e:
        print(f"[scheduler] ERROR ejecutando {module_name}: {e}")
        import traceback
        traceback.print_exc()
        return 1


def import_and_insert_from_scraper(module_name: str, source_name: str) -> int:
    """Importa datos del scraper y los inserta en la BD"""
    try:
        # Ejecutar el scraper para obtener datos
        if module_name == "pachamamaradio_local":
            from spiders.pachamamaradio_local import PachamamaRadioLocalScraper
            scraper = PachamamaRadioLocalScraper()
            news_data = scraper.scrape_news()
            # Asegurarse de obtener los datos
            if not news_data and hasattr(scraper, 'articles_data'):
                news_data = scraper.articles_data
        elif module_name == "punonoticias_local":
            from spiders.punonoticias_local import PunonoticiasLocalScraper
            scraper = PunonoticiasLocalScraper()
            news_data = scraper.scrape_news()
            # Asegurarse de obtener los datos
            if not news_data and hasattr(scraper, 'all_news'):
                news_data = scraper.all_news
        elif module_name == "sinfronteras_local":
            from spiders.sinfronteras_local import SinFronterasLocalScraper
            scraper = SinFronterasLocalScraper()
            news_data = scraper.scrape_news()
            # Asegurarse de obtener los datos
            if not news_data and hasattr(scraper, 'all_news'):
                news_data = scraper.all_news
        elif module_name == "losandes_local":
            from spiders.losandes_local import LosAndesLocalScraper
            scraper = LosAndesLocalScraper()
            news_data = scraper.scrape_news()
            if not news_data and hasattr(scraper, 'all_news'):
                news_data = scraper.all_news
        else:
            print(f"[scheduler] ERROR: Módulo desconocido: {module_name}")
            return 0
        
        if not news_data:
            print(f"[scheduler] No se obtuvieron datos de {source_name}")
            return 0
        
        # Insertar en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        inserted_count = 0
        updated_count = 0
        for article in news_data:
            try:
                # Verificar si ya existe
                url = article.get('url') or article.get('link') or article.get('href')
                if not url:
                    continue
                
                # Preparar datos del artículo
                
                contenido = article.get('contenido') or article.get('content') or article.get('texto') or ''
                resumen = article.get('resumen') or article.get('summary') or article.get('excerpt') or ''
                
                # Manejar fecha (puede ser string o datetime)
                fecha = article.get('fecha') or article.get('date')
                if fecha:
                    if isinstance(fecha, str):
                        # Intentar parsear la fecha string
                        try:
                            # Intentar con dateutil primero
                            try:
                                from dateutil import parser
                                fecha = parser.parse(fecha)
                            except ImportError:
                                # Si dateutil no está disponible, intentar formatos comunes
                                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S']:
                                    try:
                                        fecha = datetime.datetime.strptime(fecha, fmt)
                                        break
                                    except:
                                        continue
                                else:
                                    fecha = datetime.datetime.now()
                        except:
                            # Si falla, usar fecha actual
                            fecha = datetime.datetime.now()
                    elif not isinstance(fecha, datetime.datetime):
                        fecha = datetime.datetime.now()
                else:
                    fecha = datetime.datetime.now()
                
                # Manejar tags (puede ser string o lista)
                tags = article.get('tags')
                if tags:
                    if isinstance(tags, list):
                        tags = ', '.join(tags)
                    elif not isinstance(tags, str):
                        tags = str(tags)
                else:
                    tags = None
                
                # Manejar imágenes (puede ser string o lista)
                imagenes = article.get('imagenes') or article.get('images')
                if imagenes:
                    if isinstance(imagenes, list):
                        imagenes = ', '.join(imagenes)
                    elif not isinstance(imagenes, str):
                        imagenes = str(imagenes)
                else:
                    imagenes = None
                
                # Manejar categoría (puede ser lista o string muy largo)
                categoria = article.get('categoria') or article.get('category') or 'General'
                if categoria:
                    if isinstance(categoria, list):
                        categoria = ', '.join([str(c).strip() for c in categoria if c])
                    categoria = str(categoria)[:100]
                else:
                    categoria = 'General'

                # Manejar autor (límite 200 chars)
                autor = article.get('autor') or article.get('author') or 'Desconocido'
                if autor:
                    autor = str(autor)[:200]
                else:
                    autor = 'Desconocido'

                # Fuente tiene límite 100 en la BD
                fuente = source_name[:100]

                # Verificar si ya existe
                cursor.execute("SELECT id, imagenes FROM noticias WHERE url = %s", (url,))
                existing = cursor.fetchone()
                
                if existing:
                    # Ya existe - SIEMPRE actualizar cuando hay duplicados
                    # Esto asegura que el campo "imagenes" se reemplace con los nuevos datos
                    existing_id, existing_imagenes = existing
                    
                    # Actualizar siempre el campo imagenes si hay duplicados
                    # Reemplazar con lo que viene del nuevo scraping (aunque sea una URL que no sea imagen)
                    update_query = """
                    UPDATE noticias SET
                        titulo = %s,
                        fecha = %s,
                        resumen = %s,
                        contenido = %s,
                        categoria = %s,
                        autor = %s,
                        tags = %s,
                        fecha_extraccion = %s,
                        caracteres_contenido = %s,
                        palabras_contenido = %s,
                        imagenes = %s,
                        fuente = %s
                    WHERE id = %s
                    """
                    
                    update_values = (
                        article.get('titulo') or article.get('title') or 'Sin título',
                        fecha,
                        resumen[:500] if resumen else None,
                        contenido,
                        categoria,
                        autor,
                        tags,
                        datetime.datetime.now(),
                        len(contenido),
                        len(contenido.split()) if contenido else 0,
                        imagenes,  # Siempre reemplazar con el nuevo valor (aunque sea URL no-imagen)
                        fuente,
                        existing_id
                    )
                    
                    cursor.execute(update_query, update_values)
                    updated_count += 1
                else:
                    # No existe - insertar
                    insert_query = """
                    INSERT INTO noticias (
                        titulo, fecha, resumen, contenido, categoria, autor, 
                        tags, url, fecha_extraccion, caracteres_contenido, 
                        palabras_contenido, imagenes, fuente
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """
                    
                    values = (
                        article.get('titulo') or article.get('title') or 'Sin título',
                        fecha,
                        resumen[:500] if resumen else None,
                        contenido,
                        categoria,
                        autor,
                        tags,
                        url,
                        datetime.datetime.now(),
                        len(contenido),
                        len(contenido.split()) if contenido else 0,
                        imagenes,
                        fuente
                    )
                    
                    cursor.execute(insert_query, values)
                    inserted_count += 1
                
            except Exception as e:
                print(f"[scheduler] Error insertando artículo: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        total_processed = inserted_count + updated_count
        if updated_count > 0:
            print(f"[scheduler] Insertadas {inserted_count} y actualizadas {updated_count} noticias de {source_name} en la BD (Total: {total_processed})")
        else:
            print(f"[scheduler] Insertadas {inserted_count} noticias de {source_name} en la BD")
        return total_processed
        
    except Exception as e:
        print(f"[scheduler] ERROR importando datos de {module_name}: {e}")
        import traceback
        traceback.print_exc()
        return 0


def scrape_sources() -> Dict[str, Dict]:
    """Run scrapers for the 4 sites using local scrapers.
    Returns a dict with statistics for each spider."""
    # Mapeo de spiders a módulos y clases locales
    scrapers = {
        "losandes": {
            "name": "Los Andes",
            "module": "losandes_local",
            "class": "LosAndesLocalScraper"
        },
        "pachamamaradio": {
            "name": "Pachamama Radio",
            "module": "pachamamaradio_local",
            "class": "PachamamaRadioLocalScraper"
        },
        "punonoticias": {
            "name": "Puno Noticias",
            "module": "punonoticias_local",
            "class": "PunonoticiasLocalScraper"
        },
        "sinfronteras": {
            "name": "Sin Fronteras",
            "module": "sinfronteras_local",
            "class": "SinFronterasLocalScraper"
        }
    }
    
    stats = {}
    print(f"[scheduler] Running {len(scrapers)} local scrapers...")
    
    for sp_key, sp_info in scrapers.items():
        source_name = sp_info["name"]
        module_name = sp_info["module"]
        class_name = sp_info["class"]
        
        print(f"[scheduler] Running scraper: {sp_key} ({source_name})")
        
        # Contar noticias antes del scraping
        count_before = count_news_by_source(source_name)
        
        # Timestamp antes de este scraper
        spider_start_time = datetime.datetime.now()
        
        # Ejecutar scraper e insertar en BD
        inserted = import_and_insert_from_scraper(module_name, source_name)
        
        # Contar noticias después del scraping
        count_after = count_news_by_source(source_name)
        
        # Si no se insertaron pero el conteo cambió, usar el conteo
        if inserted == 0:
            inserted = count_after - count_before
        
        # Exportar noticias nuevas de esta fuente
        export_info = None
        if inserted > 0:
            export_info = export_source_news(source_name, spider_start_time)
        
        stats[sp_key] = {
            "source": source_name,
            "count_before": count_before,
            "count_after": count_after,
            "inserted": inserted,
            "status": "success" if inserted >= 0 else "error",
            "exit_code": 0 if inserted >= 0 else 1,
            "export": export_info
        }
        
        if inserted > 0:
            print(f"[scheduler] ✅ Scraper '{sp_key}' completed successfully")
            print(f"[scheduler]    Noticias insertadas: {inserted} (Total: {count_after})")
        else:
            print(f"[scheduler] ⚠️  Scraper '{sp_key}' no insertó noticias nuevas")
    
    return stats


def scrape_social() -> Dict[str, int]:
    """Trigger social scraping (upserts on URL, only new).
    Returns statistics about social news."""
    url = os.getenv("API_URL", "http://api:8000") + "/social/scrape"
    
    # Contar noticias sociales antes del scraping
    count_before = count_social_news()
    
    # Timestamp antes del scraping social
    social_start_time = datetime.datetime.now()
    
    try:
        r = requests.post(url, timeout=60)
        print(f"[scheduler] social scrape: {r.status_code} {r.text[:200]}")
        
        # Esperar un momento para que se inserten las noticias
        time.sleep(2)
        
        # Contar noticias sociales después del scraping
        count_after = count_social_news()
        inserted = count_after - count_before
        
        # Intentar obtener el número de la respuesta JSON
        try:
            response_data = r.json()
            if isinstance(response_data, dict) and "inserted" in response_data:
                inserted = response_data["inserted"]
        except:
            pass
        
        # Exportar noticias nuevas de redes sociales
        export_info = None
        if inserted > 0:
            export_info = export_social_news(social_start_time)
        
        result = {
            "count_before": count_before,
            "count_after": count_after,
            "inserted": inserted,
            "status": "success" if r.status_code == 200 else "error",
            "status_code": r.status_code,
            "export": export_info
        }
        
        return result
    except Exception as exc:
        print(f"[scheduler] Social scrape error: {exc}")
        return {
            "count_before": count_before,
            "count_after": count_before,
            "inserted": 0,
            "status": "error",
            "error": str(exc),
            "export": None
        }


def print_summary(spider_stats: Dict[str, Dict], social_stats: Dict[str, int]) -> None:
    """Imprime un resumen completo del scraping"""
    print("\n" + "="*70)
    print("📊 RESUMEN DEL SCRAPING DIARIO")
    print("="*70)
    
    # Estadísticas de spiders
    print("\n📰 NOTICIAS POR FUENTE:")
    print("-" * 70)
    total_inserted = 0
    total_errors = 0
    
    for spider_key, stats in spider_stats.items():
        source = stats["source"]
        inserted = stats["inserted"]
        total = stats["count_after"]
        status = stats["status"]
        export_info = stats.get("export")
        
        total_inserted += inserted
        if status == "error":
            total_errors += 1
        
        status_icon = "✅" if status == "success" else "❌"
        export_info_str = ""
        if export_info:
            export_info_str = f" | 📁 Exportado: {export_info['count']} noticias"
        print(f"  {status_icon} {source:20s} | Insertadas: {inserted:4d} | Total en BD: {total:5d}{export_info_str}")
    
    # Estadísticas de redes sociales
    print("\n🌐 REDES SOCIALES:")
    print("-" * 70)
    social_inserted = social_stats.get("inserted", 0)
    social_total = social_stats.get("count_after", 0)
    social_status = social_stats.get("status", "unknown")
    social_export = social_stats.get("export")
    status_icon = "✅" if social_status == "success" else "❌"
    export_info_str = ""
    if social_export:
        export_info_str = f" | 📁 Exportado: {social_export['count']} noticias"
    print(f"  {status_icon} Redes Sociales      | Insertadas: {social_inserted:4d} | Total en BD: {social_total:5d}{export_info_str}")
    
    if social_status == "error":
        total_errors += 1
    
    # Resumen total
    print("\n" + "="*70)
    print("📈 RESUMEN TOTAL:")
    print("-" * 70)
    print(f"  Total noticias insertadas (fuentes): {total_inserted}")
    print(f"  Total noticias insertadas (social):   {social_inserted}")
    print(f"  Total general insertado:              {total_inserted + social_inserted}")
    print(f"  Errores encontrados:                  {total_errors}")
    print("="*70 + "\n")


def run_daily_job() -> None:
    print(f"[scheduler] === Daily job started at {datetime.datetime.now()} ===")
    
    # Ejecutar scraping de fuentes
    spider_stats = scrape_sources()
    
    # Ejecutar scraping de redes sociales
    social_stats = scrape_social()
    
    # Mostrar resumen
    print_summary(spider_stats, social_stats)
    
    print(f"[scheduler] === Daily job finished at {datetime.datetime.now()} ===")


def seconds_until(hour: int, minute: int) -> int:
    now = datetime.datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target = target + datetime.timedelta(days=1)
    return int((target - now).total_seconds())


def wait_for_api(timeout_seconds: int = 120) -> None:
    api = os.getenv("API_URL", "http://api:8000") + "/health"
    print(f"[scheduler] Waiting for API: {api}")
    start = datetime.datetime.now()
    while (datetime.datetime.now() - start).total_seconds() < timeout_seconds:
        try:
            r = requests.get(api, timeout=5)
            if r.ok:
                print("[scheduler] API is ready")
                return
        except Exception:
            pass
        time.sleep(3)
    print("[scheduler] API not ready after timeout, continuing anyway")


def init_data_directory() -> None:
    """Inicializa el directorio de datos y sus subdirectorios"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Crear subdirectorios para cada fuente (usando los nombres exactos de las carpetas existentes)
    sources = ["losandes", "pachamamaradio", "punonoticias", "sinfronteras", "social-news"]
    for source in sources:
        (DATA_DIR / source).mkdir(parents=True, exist_ok=True)
    
    print(f"[scheduler] Directorio de datos inicializado: {DATA_DIR}")


def main() -> None:
    # Inicializar directorio de datos
    init_data_directory()
    
    # one-time run at container start (default enabled)
    run_on_start = os.getenv("RUN_ON_START", "1").lower() not in ("0", "false")

    # Daily at 06:00
    target_h, target_m = 6, 0
    print("[scheduler] Starting daily scheduler (06:00 local time)...")

    if run_on_start:
        wait_for_api()
        print("[scheduler] Running initial scrape now...")
        run_daily_job()

    while True:
        wait_s = seconds_until(target_h, target_m)
        print(f"[scheduler] Sleeping {wait_s} seconds until next run...")
        time.sleep(max(wait_s, 1))
        run_daily_job()


if __name__ == "__main__":
    main()


