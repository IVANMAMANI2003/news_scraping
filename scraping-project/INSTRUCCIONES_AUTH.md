# 🔐 Instrucciones de Configuración - Sistema de Autenticación

## 📋 Pasos para Configurar el Sistema

### 1. Instalar Dependencias de Autenticación

Ejecuta uno de estos comandos:

**Opción A: Usando el script batch (Windows)**
```bash
install_auth_dependencies.bat
```

**Opción B: Manualmente**
```bash
cd scraping-project
venv\Scripts\python.exe -m pip install bcrypt==4.1.2 PyJWT==2.8.0
```

### 2. Inicializar el Esquema de Base de Datos

Ejecuta el script para crear las tablas necesarias:

```bash
cd scraping-project
venv\Scripts\python.exe api\scripts\init_auth_schema.py
```

Este script creará:
- Tabla `usuarios`
- Tabla `api_keys`
- Tabla `permisos`
- Tabla `usuario_permisos`
- Tabla `sesiones`
- Tabla `search_history`
- Usuario admin por defecto

### 3. Verificar que el Servidor Funciona

Inicia el servidor API:

```bash
cd scraping-project
venv\Scripts\python.exe -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Deberías ver:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 4. Acceder al Panel de Administración

1. Abre tu navegador en: `http://localhost:8080/admin/login.html`
2. Usa las credenciales:
   - **Email**: `admin@biznews.com`
   - **Password**: `admin123`

### 5. Endpoints Disponibles

#### Autenticación
- `POST /auth/register` - Registrar nuevo usuario
- `POST /auth/login` - Iniciar sesión
- `POST /auth/refresh` - Refrescar token
- `POST /auth/logout` - Cerrar sesión
- `GET /auth/me` - Obtener usuario actual

#### Usuarios (requiere autenticación)
- `GET /users` - Listar usuarios
- `GET /users/{id}` - Obtener usuario
- `POST /users` - Crear usuario (solo admin)
- `PUT /users/{id}` - Actualizar usuario
- `DELETE /users/{id}` - Eliminar usuario (solo admin)

#### API Keys (requiere autenticación)
- `GET /api-keys` - Listar API keys
- `GET /api-keys/{id}` - Obtener API key
- `POST /api-keys` - Crear API key
- `PUT /api-keys/{id}` - Actualizar API key
- `DELETE /api-keys/{id}` - Eliminar API key
- `GET /api-keys/{id}/stats` - Estadísticas de uso

## 🔑 Credenciales por Defecto

**Usuario Admin:**
- Email: `admin@biznews.com`
- Password: `admin123`
- Rol: `admin`
- Plan: `enterprise`

⚠️ **IMPORTANTE**: Cambia la contraseña del admin en producción.

## 📝 Notas Importantes

1. **Hash de Contraseña**: El hash en el SQL es válido para "admin123", pero en producción deberías generar uno nuevo usando:
   ```python
   import bcrypt
   print(bcrypt.hashpw(b'tu_password', bcrypt.gensalt()).decode())
   ```

2. **JWT Secret Key**: El sistema usa una clave secreta generada automáticamente. En producción, configura `JWT_SECRET_KEY` en las variables de entorno.

3. **CORS**: Asegúrate de que el frontend esté en los orígenes permitidos en `main.py`.

## 🐛 Solución de Problemas

### Error: "No module named 'bcrypt'"
```bash
venv\Scripts\python.exe -m pip install bcrypt==4.1.2 PyJWT==2.8.0
```

### Error: "Table already exists"
El esquema ya está inicializado. Esto es normal si ya ejecutaste el script antes.

### Error: "Invalid credentials"
Verifica que el usuario admin existe en la base de datos:
```sql
SELECT * FROM usuarios WHERE email = 'admin@biznews.com';
```

### Error de conexión a la base de datos
Verifica las variables de entorno o el archivo `.env`:
- `PGHOST`
- `PGPORT`
- `PGDATABASE`
- `PGUSER`
- `PGPASSWORD`

## 📚 Documentación de la API

Una vez que el servidor esté corriendo, puedes acceder a la documentación interactiva en:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

