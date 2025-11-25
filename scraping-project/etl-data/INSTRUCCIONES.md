# 📋 INSTRUCCIONES PARA MIGRAR DE `noticias` A `noticias_limpia`

## 🚀 OPCIÓN RÁPIDA (Recomendada)

**Ejecuta un solo script que hace todo automáticamente:**

```bash
cd scraping-project/etl-data
python migrate_completo.py
```

Este script:
1. ✅ Exporta datos de `noticias` a CSV
2. ✅ Normaliza los datos automáticamente
3. ✅ Crea la tabla `noticias_limpia` y carga los datos

**¡No necesitas editar ningún archivo!**

---

## 🔄 Flujo Manual (Paso a Paso)

### Paso 1: Exportar datos de `noticias` a CSV
**Archivo:** `export_csv_mejorado.py`

```bash
cd scraping-project/etl-data
python export_csv_mejorado.py
```

**Opciones:**
- Opción 1: Exportar todos los datos a un solo CSV
- Opción 2: Exportar datos separados por fuente
- Opción 3: Exportar todo (opciones 1 y 2)

**Resultado:** Genera archivo `noticias_YYYYMMDD_HHMMSS.csv` en la carpeta `etl-data`

---

### Paso 2: Normalizar los datos
**Archivo:** `data-normalizer.py`

**⚠️ IMPORTANTE:** Antes de ejecutar, edita el archivo y cambia el nombre del archivo de entrada:

```python
# Línea 318, cambiar:
input_file = "noticias_20251014_062537.csv"  # ← Cambiar por el nombre del CSV generado en el Paso 1
```

**Ejecutar:**
```bash
python data-normalizer.py
```

**Resultado:** Genera archivo `data_etl_final_YYYYMMDD_HHMMSS.csv` con datos normalizados

---

### Paso 3: Crear tabla `noticias_limpia` y cargar datos
**Archivo:** `create_clean_table.py`

**⚠️ IMPORTANTE:** Antes de ejecutar, edita el archivo y cambia el nombre del archivo CSV:

```python
# Línea 284, cambiar:
csv_file = "data_etl_final_20251014_070213.csv"  # ← Cambiar por el nombre del CSV generado en el Paso 2
```

**Ejecutar:**
```bash
python create_clean_table.py
```

**Resultado:** 
- Crea la tabla `noticias_limpia` si no existe
- Carga todos los datos normalizados
- Muestra estadísticas de verificación

---

## 📝 Resumen de Archivos

| Archivo | Propósito | Cuándo ejecutar |
|---------|-----------|-----------------|
| `export_csv_mejorado.py` | Exporta `noticias` → CSV | Primero |
| `data-normalizer.py` | Normaliza y transforma CSV | Segundo |
| `create_clean_table.py` | Crea tabla y carga datos | Tercero |
| `integrate_new_news.py` | Agrega nuevas noticias | Para actualizaciones futuras |

---

## 🚀 Ejecución Rápida (una vez configurados los nombres de archivos)

```bash
# 1. Exportar
python export_csv_mejorado.py
# (Seleccionar opción 1)

# 2. Normalizar (editar nombre de archivo primero)
python data-normalizer.py

# 3. Crear tabla y cargar (editar nombre de archivo primero)
python create_clean_table.py
```

---

## ⚠️ Notas Importantes

1. **Pandas requerido:** Asegúrate de tener pandas y numpy instalados:
   ```bash
   pip install pandas numpy
   ```

2. **Nombres de archivos:** Los archivos generan nombres con timestamps, así que necesitas actualizar manualmente los nombres en los scripts del Paso 2 y 3.

3. **Duplicados:** El sistema maneja duplicados automáticamente por URL.

4. **Base de datos:** Todos los scripts usan:
   - Host: localhost
   - Database: noticias
   - User: postgres
   - Password: 123456

