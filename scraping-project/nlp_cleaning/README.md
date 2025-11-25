# Módulo de Limpieza Avanzada de Noticias con Ollama

Este módulo implementa un sistema de limpieza de contenido de noticias usando **Ollama** con el modelo **deepseek-r1:8b** para seleccionar párrafos relevantes basándose en el título y resumen de la noticia.

## 🎯 Objetivo

Dado un título, un resumen y un contenido RAW extraído por scraping, el sistema:
1. Envía una única petición a Ollama (modelo deepseek-r1:8b)
2. Pasa el título, resumen y contenido RAW
3. Hace que Ollama seleccione los párrafos realmente relevantes
4. Retorna un JSON con párrafos relevantes, irrelevantes y texto limpio

## 📋 Requisitos Previos

### 1. Instalar Ollama

Descarga e instala Ollama desde: https://ollama.ai

### 2. Descargar el Modelo

```bash
ollama pull deepseek-r1:8b
```

### 3. Verificar que Ollama esté corriendo

```bash
ollama list
```

Deberías ver `deepseek-r1:8b` en la lista.

## 🔧 Instalación de Dependencias

```bash
cd scraping-project/nlp_cleaning
pip install -r requirements.txt
```

O instalar manualmente:
```bash
pip install ollama psycopg2-binary python-dotenv
```

## 🚀 Uso Básico

### Función Principal: `clean_news()`

```python
from nlp_cleaning import clean_news

# Ejemplo de uso
result = clean_news(
    title="Nueva tecnología en inteligencia artificial",
    summary="Se presenta un nuevo modelo de IA que revoluciona el procesamiento de lenguaje natural",
    raw="""Contenido RAW extraído del scraping...
    
    [Publicidad] Este es un anuncio que no es relevante...
    
    Más contenido relevante sobre la noticia...
    """
)

# Resultado
print(result['relevantes'])      # Lista de párrafos relevantes
print(result['irrelevantes'])    # Lista de párrafos irrelevantes
print(result['clean_text'])      # Texto limpio (párrafos relevantes unidos)
```

### Uso con Clase NLPContentCleaner

```python
from nlp_cleaning import NLPContentCleaner

# Inicializar limpiador
cleaner = NLPContentCleaner(
    model_name="deepseek-r1:8b",
    ollama_base_url=None  # None = http://localhost:11434
)

# Limpiar contenido
result = cleaner.clean_news(
    title="Título de la noticia",
    summary="Resumen de la noticia",
    raw="Contenido RAW..."
)
```

## 📊 Formato de Salida

```python
{
    "relevantes": [
        "Párrafo 1 relevante...",
        "Párrafo 2 relevante...",
        ...
    ],
    "irrelevantes": [
        "Párrafo publicitario...",
        "Contenido no relacionado...",
        ...
    ],
    "clean_text": "Párrafo 1 relevante...\n\nPárrafo 2 relevante...\n\n..."
}
```

## 🔧 Integración con Base de Datos

### Procesar Noticias Existentes

```bash
# Procesar todas las noticias de la tabla 'noticias'
python integrate_db.py

# Procesar desde 'noticias_limpia'
python integrate_db.py --source-table noticias_limpia

# Procesar solo las primeras 10 noticias (recomendado para probar)
python integrate_db.py --limit 10

# Usar URL personalizada de Ollama
python integrate_db.py --ollama-url http://localhost:11434

# No omitir noticias ya procesadas (reprocesar todo)
python integrate_db.py --no-skip-processed
```

### Opciones de Línea de Comandos

```bash
python integrate_db.py \
    --source-table noticias \
    --batch-size 10 \
    --limit 100 \
    --model-name deepseek-r1:8b \
    --ollama-url http://localhost:11434
```

**Nota:** El `batch_size` por defecto es 10 porque las peticiones a Ollama pueden ser lentas. Ajusta según tu hardware.

## 🗄️ Tabla de Base de Datos

El script `integrate_db.py` crea automáticamente la tabla `noticias_bert_clean`:

```sql
CREATE TABLE noticias_bert_clean (
    id SERIAL PRIMARY KEY,
    noticia_id INTEGER,
    titulo TEXT NOT NULL,
    resumen TEXT,
    contenido_raw TEXT,
    contenido_limpio TEXT,
    parrafos_relevantes JSONB,
    parrafos_irrelevantes JSONB,
    num_parrafos_total INTEGER,
    num_parrafos_relevantes INTEGER,
    num_parrafos_irrelevantes INTEGER,
    procesado_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    url TEXT,
    fuente VARCHAR(100),
    fecha TIMESTAMP,
    modelo_usado VARCHAR(50) DEFAULT 'deepseek-r1:8b'
);
```

## 📁 Estructura del Módulo

```
nlp_cleaning/
├── __init__.py              # Exports principales
├── nlp_cleaner.py          # Módulo principal con NLPContentCleaner
├── integrate_db.py          # Script de integración con BD
├── example_usage.py         # Ejemplos de uso
├── test_quick.py           # Script de prueba rápida
├── requirements.txt         # Dependencias
└── README.md               # Esta documentación
```

## 🔍 Funciones Principales

### `NLPContentCleaner.clean_news(title, summary, raw)`
Método principal que limpia noticias usando Ollama.

### `clean_news(title, summary, raw, model_name, ollama_base_url)`
Función de conveniencia que encapsula el uso de la clase.

## ⚙️ Configuración

### Variables de Entorno

```bash
# Base de datos
export PGHOST=127.0.0.1
export PGPORT=5432
export PGDATABASE=noticias
export PGUSER=postgres
export PGPASSWORD=123456

# Ollama (opcional, por defecto usa http://localhost:11434)
export OLLAMA_BASE_URL=http://localhost:11434
```

### Modelos Disponibles

Puedes usar diferentes modelos de Ollama:
- `deepseek-r1:8b` (recomendado, usado por defecto)
- `llama3:8b`
- `mistral:7b`
- Cualquier otro modelo compatible con Ollama

Para cambiar el modelo:
```python
cleaner = NLPContentCleaner(model_name="llama3:8b")
```

## 📈 Rendimiento

- **Velocidad:** Depende del hardware y del modelo. Con `deepseek-r1:8b` en CPU: ~5-15 segundos por noticia.
- **Batch Size:** Recomendado 10 noticias por lote para evitar sobrecarga.
- **GPU:** Si tienes GPU, Ollama la usará automáticamente para acelerar el procesamiento.

## 🐛 Solución de Problemas

### Error: "Connection refused" o "Cannot connect to Ollama"
- Asegúrate de que Ollama esté corriendo: `ollama serve` (o inicia la aplicación)
- Verifica la URL: por defecto es `http://localhost:11434`

### Error: "Model not found"
- Descarga el modelo: `ollama pull deepseek-r1:8b`
- Verifica que esté disponible: `ollama list`

### Error: "JSON decode error"
- El modelo puede devolver texto adicional. El parser intenta extraer el JSON automáticamente.
- Si persiste, revisa los logs para ver la respuesta completa.

### Procesamiento muy lento
- Reduce el `batch_size` a 5 o menos
- Considera usar un modelo más pequeño si tienes hardware limitado
- Usa GPU si está disponible (Ollama la detecta automáticamente)

## 📝 Ejemplos

Ver el archivo `example_usage.py` para más ejemplos de uso.

## 🔄 Cambios desde la Versión Anterior

Esta versión (2.0.0) reemplaza completamente el sistema anterior basado en BERT:

- ❌ **Eliminado:** BERT, embeddings, clasificadores, entrenamiento
- ✅ **Nuevo:** Integración con Ollama usando deepseek-r1:8b
- ✅ **Nuevo:** Procesamiento más inteligente y contextual
- ✅ **Nuevo:** Sin necesidad de entrenar modelos

## 🤝 Contribuciones

Este módulo fue desarrollado como parte del sistema de scraping de noticias.

## 📄 Licencia

Mismo licencia que el proyecto principal.
