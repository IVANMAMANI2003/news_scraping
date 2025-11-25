"""
Módulo principal de limpieza de noticias usando Ollama (deepseek-r1:8b)

Este módulo implementa un sistema de limpieza de contenido que utiliza
Ollama para seleccionar párrafos relevantes basándose en el título y resumen.
"""

import json
import logging
import re
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NLPContentCleaner:
    """
    Clase principal para limpieza de noticias usando Ollama.
    
    Utiliza el modelo deepseek-r1:8b para analizar y seleccionar
    párrafos relevantes del contenido de noticias.
    """
    
    def __init__(
        self,
        model_name: str = "deepseek-r1:8b",
        ollama_base_url: Optional[str] = None,
        timeout: int = 300  # 5 minutos por defecto
    ):
        """
        Inicializa el limpiador de noticias.
        
        Args:
            model_name: Nombre del modelo de Ollama a usar
            ollama_base_url: URL base de Ollama (default: http://localhost:11434)
            timeout: Timeout en segundos para las peticiones
        """
        if requests is None:
            raise ImportError(
                "La librería 'requests' no está instalada. "
                "Instálala con: pip install requests"
            )
        
        self.model_name = model_name
        self.timeout = timeout
        self.ollama_base_url = (ollama_base_url or "http://localhost:11434").rstrip('/')
        
        # Verificar conexión con Ollama (igual que en tu otro proyecto)
        self._check_connection()
        
        logger.info(f"✅ NLPContentCleaner inicializado con modelo: {model_name}")
        logger.info(f"   URL base: {self.ollama_base_url}")
    
    def _check_connection(self):
        """
        Verifica la conexión con Ollama (igual que en tu otro proyecto).
        
        Raises:
            ConnectionError: Si no se puede conectar a Ollama.
        """
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Conectado a Ollama en {self.ollama_base_url}")
                # Verificar que el modelo esté disponible
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                if self.model_name not in model_names:
                    logger.warning(f"⚠️  Advertencia: Modelo '{self.model_name}' no encontrado en Ollama")
                    logger.warning(f"   Modelos disponibles: {', '.join(model_names[:5])}")
            else:
                raise ConnectionError(f"Ollama respondió con código {response.status_code}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"No se pudo conectar a Ollama en {self.ollama_base_url}. "
                f"Asegúrate de que Ollama esté ejecutándose."
            )
        except Exception as e:
            raise ConnectionError(f"Error al verificar conexión con Ollama: {e}")
    
    def _build_prompt(self, title: str, summary: str, content: str) -> str:
        """
        Construye el prompt para Ollama.
        
        Args:
            title: Título de la noticia
            summary: Resumen de la noticia
            content: Contenido RAW de la noticia
        
        Returns:
            Prompt formateado
        """
        # Prompt optimizado para trabajar con oraciones
        # El contenido puede venir en un solo bloque, necesitamos dividirlo en oraciones
        prompt = f"""Analiza esta noticia y separa ORACIONES relevantes de irrelevantes.

IMPORTANTE: El contenido puede venir todo junto. Primero DIVÍDELO en oraciones (separadas por puntos, signos de interrogación o exclamación).

Título: {title}
Resumen: {summary}
Contenido (puede estar todo junto, sin separaciones):
{content}

INSTRUCCIONES:
1. Divide el contenido en ORACIONES individuales (cada oración termina en punto, signo de interrogación o exclamación).
2. Analiza cada oración para determinar si es relevante al título y resumen.
3. Clasifica cada oración como relevante o irrelevante.
4. Excluye: publicidad, anuncios, texto duplicado, comentarios de redes sociales, enlaces, contenido fuera del tema.

IMPORTANTE: Devuelve SOLO un JSON válido. Cada string debe estar correctamente entre comillas dobles.

Formato JSON exacto (sin markdown, sin texto adicional):
{{
  "relevantes": ["oración relevante 1.", "oración relevante 2.", "oración relevante 3."],
  "irrelevantes": ["oración publicitaria.", "comentario de Facebook.", "texto no relacionado."],
  "clean_text": "oración relevante 1.\\n\\noración relevante 2.\\n\\noración relevante 3."
}}

Reglas CRÍTICAS:
- Cada string debe estar entre comillas dobles: "texto"
- NO uses comillas dobles dentro de las strings (usa comillas simples si es necesario)
- NO agregues comillas dobles extra al final de strings
- Cada elemento debe ser una ORACIÓN completa (termina en punto).
- NO reescribas las oraciones, usa exactamente como aparecen en el contenido original.
- Responde SOLO con el JSON, sin ```json, sin markdown, sin texto antes o después."""
        
        return prompt
    
    def _parse_ollama_response(self, response_text: str) -> Dict:
        """
        Parsea la respuesta de Ollama y extrae el JSON.
        
        Args:
            response_text: Texto de respuesta de Ollama
        
        Returns:
            Diccionario con los datos parseados
        """
        # Limpiar el texto de respuesta
        response_text = response_text.strip()
        
        # Eliminar markdown code blocks si existen (```json ... ```)
        response_text = re.sub(r'^```json\s*', '', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'^```\s*', '', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'```\s*$', '', response_text, flags=re.MULTILINE)
        response_text = response_text.strip()
        
        # Intentar extraer JSON del texto (puede venir con markdown o texto adicional)
        # Buscar el JSON entre llaves
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
        else:
            # Si no se encuentra, intentar parsear directamente
            json_str = response_text
        
        try:
            # Intentar parsear JSON directamente
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # Si falla, intentar arreglar strings sin terminar
            logger.warning(f"⚠️ Error parseando JSON, intentando reparar... Error: {e}")
            
            try:
                # Paso 1: Arreglar comillas dobles múltiples al final de strings
                # Buscar patrones como: "texto"" o "texto""
                json_str = re.sub(r'("")\s*"', r'"', json_str)  # "" " -> "
                json_str = re.sub(r'([^\\])("")([^"])', r'\1"\3', json_str)  # "" -> " (excepto si es \")
                
                # Paso 2: Arreglar strings que terminan con comilla doble doble antes de comas/llaves
                json_str = re.sub(r'""\s*([,}\]])', r'"\1', json_str)
                
                # Paso 3: Buscar y cerrar strings sin terminar en arrays
                # Patrón: "texto sin cerrar seguido de coma o cierre
                def fix_unterminated_string(match):
                    content = match.group(1)
                    # Si el contenido no termina con comilla, agregarla
                    if not content.endswith('"'):
                        # Buscar el final lógico (coma, corchete, llave)
                        return f'"{content}"'
                    return match.group(0)
                
                # Arreglar strings en arrays que no terminan correctamente
                json_str = re.sub(r'"([^"]*?)(?=\s*[,}\]])', lambda m: f'"{m.group(1)}"', json_str)
                
                # Paso 4: Intentar parsear de nuevo
                data = json.loads(json_str)
                
            except json.JSONDecodeError as e2:
                logger.error(f"❌ No se pudo reparar el JSON. Error: {e2}")
                logger.error(f"JSON recibido (primeros 1500 chars):\n{json_str[:1500]}")
                
                # Último intento: extraer manualmente los arrays usando regex
                try:
                    logger.info("🔧 Intentando extracción manual de arrays...")
                    
                    # Buscar el bloque de "relevantes"
                    relevantes_match = re.search(r'"relevantes"\s*:\s*\[(.*?)(?:\]|$)', json_str, re.DOTALL)
                    # Buscar el bloque de "irrelevantes"  
                    irrelevantes_match = re.search(r'"irrelevantes"\s*:\s*\[(.*?)(?:\]|$)', json_str, re.DOTALL)
                    
                    relevantes = []
                    irrelevantes = []
                    
                    def extract_strings_from_array(array_content):
                        """Extrae strings de un array, incluso si están mal formadas."""
                        strings = []
                        # Buscar patrones de strings: "texto" o "texto""
                        # Incluir strings que pueden tener comillas dobles al final
                        pattern = r'"([^"]*(?:""[^"]*)*)"'
                        matches = re.finditer(pattern, array_content)
                        
                        for match in matches:
                            text = match.group(1)
                            # Limpiar comillas dobles dobles
                            text = text.replace('""', '"')
                            # Limpiar escapes
                            text = text.replace('\\"', '"')
                            text = text.replace('\\n', '\n')
                            if text.strip():
                                strings.append(text.strip())
                        
                        # Si no encontramos strings bien formadas, intentar extraer texto entre comillas
                        if not strings:
                            # Buscar cualquier texto entre comillas, incluso sin cerrar
                            pattern2 = r'"([^"]*?)(?:"|,|\]|$)'
                            matches2 = re.finditer(pattern2, array_content)
                            for match in matches2:
                                text = match.group(1).strip()
                                if text and len(text) > 5:  # Solo strings con contenido significativo
                                    text = text.replace('""', '"')
                                    strings.append(text)
                        
                        return strings
                    
                    if relevantes_match:
                        contenido = relevantes_match.group(1)
                        relevantes = extract_strings_from_array(contenido)
                        logger.info(f"   📝 Encontradas {len(relevantes)} oraciones relevantes")
                    
                    if irrelevantes_match:
                        contenido = irrelevantes_match.group(1)
                        irrelevantes = extract_strings_from_array(contenido)
                        logger.info(f"   📝 Encontradas {len(irrelevantes)} oraciones irrelevantes")
                    
                    if relevantes or irrelevantes:
                        # Construir clean_text agrupando oraciones
                        if relevantes:
                            # Agrupar de 2 en 2 para formar párrafos
                            parrafos = []
                            for i in range(0, len(relevantes), 2):
                                grupo = relevantes[i:i+2]
                                parrafo = " ".join(grupo)
                                parrafos.append(parrafo)
                            clean_text = "\n\n".join(parrafos)
                        else:
                            clean_text = ""
                        
                        logger.info(f"✅ Extracción manual exitosa: {len(relevantes)} relevantes, {len(irrelevantes)} irrelevantes")
                        return {
                            "relevantes": relevantes,
                            "irrelevantes": irrelevantes,
                            "clean_text": clean_text
                        }
                    else:
                        logger.warning("⚠️ No se pudieron extraer oraciones del JSON mal formado")
                
                except Exception as e3:
                    logger.error(f"❌ Error en extracción manual: {e3}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # Retornar estructura vacía como último recurso
                logger.error("❌ No se pudo extraer ningún contenido del JSON")
                return {
                    "relevantes": [],
                    "irrelevantes": [],
                    "clean_text": ""
                }
        
        # Validar estructura
        try:
            if not isinstance(data, dict):
                raise ValueError("La respuesta no es un diccionario")
            
            # Asegurar que tiene las claves necesarias
            result = {
                "relevantes": data.get("relevantes", []),
                "irrelevantes": data.get("irrelevantes", []),
                "clean_text": data.get("clean_text", "")
            }
            
            # Validar tipos
            if not isinstance(result["relevantes"], list):
                result["relevantes"] = []
            if not isinstance(result["irrelevantes"], list):
                result["irrelevantes"] = []
            if not isinstance(result["clean_text"], str):
                result["clean_text"] = ""
            
            # Si clean_text está vacío pero hay relevantes, construirlo
            # Agrupar oraciones en párrafos lógicos (2-3 oraciones por párrafo)
            if not result["clean_text"] and result["relevantes"]:
                # Unir oraciones relevantes, agrupando cada 2-3 oraciones en párrafos
                oraciones = result["relevantes"]
                parrafos = []
                for i in range(0, len(oraciones), 2):  # Agrupar de 2 en 2
                    grupo = oraciones[i:i+2]
                    parrafo = " ".join(grupo)
                    parrafos.append(parrafo)
                result["clean_text"] = "\n\n".join(parrafos)
            
            return result
            
        except (ValueError, KeyError) as e:
            logger.error(f"❌ Error validando estructura JSON: {e}")
            logger.error(f"Respuesta recibida: {response_text[:500]}")
            # Retornar estructura vacía en caso de error
            return {
                "relevantes": [],
                "irrelevantes": [],
                "clean_text": ""
            }
    
    def clean_news(
        self,
        title: str,
        summary: str,
        raw: str
    ) -> Dict[str, any]:
        """
        Limpia el contenido de una noticia usando Ollama.
        
        Args:
            title: Título de la noticia
            summary: Resumen de la noticia
            raw: Contenido RAW extraído del scraping
        
        Returns:
            Diccionario con:
                - relevantes: Lista de párrafos relevantes
                - irrelevantes: Lista de párrafos irrelevantes
                - clean_text: Texto limpio (párrafos relevantes unidos)
        """
        # Validar entradas
        if not title or not title.strip():
            logger.warning("⚠️ Título vacío, usando placeholder")
            title = "Sin título"
        
        if not summary or not summary.strip():
            logger.warning("⚠️ Resumen vacío")
            summary = ""
        
        if not raw or not raw.strip():
            logger.warning("⚠️ Contenido RAW vacío")
            return {
                "relevantes": [],
                "irrelevantes": [],
                "clean_text": ""
            }
        
        # Construir prompt
        prompt = self._build_prompt(title, summary, raw)
        
        try:
            logger.info(f"📤 Enviando petición a Ollama (modelo: {self.model_name})...")
            
            # Usar requests directamente para llamar a la API HTTP de Ollama
            # Siguiendo EXACTAMENTE el mismo patrón que tu otro proyecto
            url = f"{self.ollama_base_url}/api/generate"
            
            # Pasar opciones directamente en el payload (no dentro de "options")
            # Igual que en tu otro proyecto: payload = {"model": ..., "prompt": ..., "stream": ..., **kwargs}
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,  # Primero intentar sin streaming (más simple)
                "temperature": 0.1,
                "num_predict": 10096,  # Aumentar tokens para modelos de razonamiento
                "top_p": 0.9,
            }
            
            logger.debug(f"URL: {url}")
            logger.debug(f"Modelo: {self.model_name}")
            logger.debug(f"Longitud del prompt: {len(prompt)} caracteres")
            
            # Hacer la petición HTTP POST (sin streaming primero, como en tu proyecto)
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            # Verificar que la petición fue exitosa
            response.raise_for_status()
            
            # Parsear la respuesta JSON (igual que en tu proyecto)
            result = response.json()
            
            # Extraer el texto de la respuesta (igual que en tu proyecto)
            response_text = result.get('response', '').strip()
            
            # Si response está vacío pero done_reason es 'length', el modelo se quedó sin tokens
            # Verificar si hay 'thinking' que podamos usar
            if not response_text:
                done_reason = result.get('done_reason', '')
                if done_reason == 'length':
                    thinking = result.get('thinking', '')
                    if thinking and len(str(thinking)) > 100:
                        logger.warning("⚠️ Modelo alcanzó límite de tokens, pero hay 'thinking'")
                        logger.warning("   Aumentando num_predict y reintentando...")
                        # Aumentar tokens y reintentar (actualizar directamente en payload)
                        payload["num_predict"] = 16384
                        response = requests.post(
                            url,
                            json=payload,
                            timeout=self.timeout
                        )
                        response.raise_for_status()
                        result = response.json()
                        response_text = result.get('response', '').strip()
            
            # Si no hay respuesta, intentar con streaming
            if not response_text:
                logger.warning("⚠️ Respuesta vacía sin streaming, intentando con streaming...")
                payload["stream"] = True
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                    stream=True
                )
                response.raise_for_status()
                
                # Capturar todos los chunks del stream (igual que en tu proyecto)
                response_text = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            chunk_text = chunk.get('response', '')
                            if chunk_text:
                                response_text += chunk_text
                        except json.JSONDecodeError:
                            continue
                
                response_text = response_text.strip()
            
            # Log del resultado
            if response_text:
                logger.info(f"✅ Respuesta obtenida ({len(response_text)} caracteres)")
                logger.debug(f"Primeros 200 chars: {response_text[:200]}")
            else:
                logger.error("❌ Respuesta vacía de Ollama")
                logger.error(f"   Campo 'response': '{response_text}'")
                logger.error(f"   Campo 'done': {result.get('done', 'N/A')}")
                logger.error(f"   Campo 'done_reason': {result.get('done_reason', 'N/A')}")
                logger.error(f"   Claves en resultado: {list(result.keys())}")
            
            # Validar respuesta
            if not response_text or not response_text.strip():
                logger.error("❌ Respuesta vacía de Ollama después de todos los intentos")
                logger.error("   Verifica que Ollama esté corriendo y el modelo esté disponible")
                return {
                    "relevantes": [],
                    "irrelevantes": [],
                    "clean_text": ""
                }
            
            logger.info(f"✅ Respuesta recibida de Ollama ({len(response_text)} caracteres)")
            logger.debug(f"Primeros 200 chars: {response_text[:200]}")
            
            # Parsear respuesta
            result = self._parse_ollama_response(response_text)
            
            logger.info(
                f"📊 Resultado: {len(result['relevantes'])} oraciones relevantes, "
                f"{len(result['irrelevantes'])} irrelevantes"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error al comunicarse con Ollama: {e}")
            logger.error(f"   Asegúrate de que Ollama esté corriendo y el modelo {self.model_name} esté disponible")
            
            # Retornar estructura vacía en caso de error
            return {
                "relevantes": [],
                "irrelevantes": [],
                "clean_text": ""
            }


# Instancia global del limpiador (lazy loading)
_cleaner_instance: Optional[NLPContentCleaner] = None


def get_cleaner_instance(
    model_name: str = "deepseek-r1:8b",
    ollama_base_url: Optional[str] = None,
    timeout: int = 300  # 5 minutos por defecto
) -> NLPContentCleaner:
    """
    Obtiene una instancia singleton del limpiador.
    
    Args:
        model_name: Nombre del modelo de Ollama
        ollama_base_url: URL base de Ollama
        timeout: Timeout en segundos
    
    Returns:
        Instancia de NLPContentCleaner
    """
    global _cleaner_instance
    
    if _cleaner_instance is None:
        _cleaner_instance = NLPContentCleaner(
            model_name=model_name,
            ollama_base_url=ollama_base_url,
            timeout=timeout
        )
    
    return _cleaner_instance


def clean_news(
    title: str,
    summary: str,
    raw: str,
    model_name: str = "deepseek-r1:8b",
    ollama_base_url: Optional[str] = None
) -> Dict[str, any]:
    """
    Función principal para limpiar noticias usando Ollama.
    
    Esta es la función de entrada principal del módulo. Toma un título,
    resumen y contenido RAW, y devuelve el contenido limpio con solo
    los párrafos relevantes seleccionados por Ollama.
    
    Args:
        title: Título de la noticia
        summary: Resumen de la noticia
        raw: Contenido RAW extraído del scraping
        model_name: Nombre del modelo de Ollama (default: deepseek-r1:8b)
        ollama_base_url: URL base de Ollama (opcional)
    
    Returns:
        Diccionario con:
            - relevantes: Lista de párrafos relevantes
            - irrelevantes: Lista de párrafos irrelevantes
            - clean_text: Texto limpio (párrafos relevantes unidos)
    
    Example:
        >>> result = clean_news(
        ...     title="Nueva tecnología en IA",
        ...     summary="Se presenta un nuevo modelo de IA",
        ...     raw="Párrafo 1...\\n\\nPárrafo 2...\\n\\nPublicidad..."
        ... )
        >>> print(result['clean_text'])
        >>> print(result['relevantes'])
    """
    # Obtener instancia del limpiador
    cleaner = get_cleaner_instance(
        model_name=model_name,
        ollama_base_url=ollama_base_url
    )
    
    # Limpiar contenido
    result = cleaner.clean_news(title, summary, raw)
    
    return result

