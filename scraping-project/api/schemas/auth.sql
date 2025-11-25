-- ============================================
-- Esquema de Autenticación y Gestión de Usuarios
-- ============================================

-- Tabla de Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255),
    activo BOOLEAN DEFAULT true,
    rol VARCHAR(50) DEFAULT 'user' CHECK (rol IN ('admin', 'user', 'moderator')),
    plan VARCHAR(50) DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'business', 'enterprise')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    email_verificado BOOLEAN DEFAULT false
);

-- Tabla de API Keys
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    key VARCHAR(255) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'business', 'enterprise')),
    activo BOOLEAN DEFAULT true,
    requests_today INT DEFAULT 0,
    requests_total BIGINT DEFAULT 0,
    last_reset DATE DEFAULT CURRENT_DATE,
    last_used TIMESTAMP,
    fuente_permitida VARCHAR(100),
    max_sources INT DEFAULT 1,
    keywords TEXT[],
    webhook_url VARCHAR(500),
    historial_dias INT DEFAULT 0,
    limite_diario INT DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Tabla de Permisos
CREATE TABLE IF NOT EXISTS permisos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Permisos de Usuario (Many-to-Many)
CREATE TABLE IF NOT EXISTS usuario_permisos (
    usuario_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    permiso_id INT NOT NULL REFERENCES permisos(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INT REFERENCES usuarios(id),
    PRIMARY KEY (usuario_id, permiso_id)
);

-- Tabla de Sesiones
CREATE TABLE IF NOT EXISTS sesiones (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    refresh_token VARCHAR(500) UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Tabla de Historial de Búsquedas (para planes PRO+)
CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    api_key_id INT REFERENCES api_keys(id) ON DELETE CASCADE,
    usuario_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
    query_params JSONB NOT NULL,
    results_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios(activo);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS idx_api_keys_usuario ON api_keys(usuario_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_activo ON api_keys(activo);
CREATE INDEX IF NOT EXISTS idx_sesiones_token ON sesiones(token);
CREATE INDEX IF NOT EXISTS idx_sesiones_usuario ON sesiones(usuario_id);
CREATE INDEX IF NOT EXISTS idx_search_history_api_key ON search_history(api_key_id);
CREATE INDEX IF NOT EXISTS idx_search_history_usuario ON search_history(usuario_id);
CREATE INDEX IF NOT EXISTS idx_search_history_created ON search_history(created_at);

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Eliminar trigger si existe antes de crearlo
DROP TRIGGER IF EXISTS update_usuarios_updated_at ON usuarios;
CREATE TRIGGER update_usuarios_updated_at BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insertar permisos básicos
INSERT INTO permisos (nombre, descripcion) VALUES
    ('admin.full', 'Acceso completo al sistema'),
    ('users.read', 'Leer usuarios'),
    ('users.write', 'Crear/editar usuarios'),
    ('users.delete', 'Eliminar usuarios'),
    ('api_keys.read', 'Leer API keys'),
    ('api_keys.write', 'Crear/editar API keys'),
    ('api_keys.delete', 'Eliminar API keys'),
    ('news.read', 'Leer noticias'),
    ('news.write', 'Crear/editar noticias'),
    ('news.delete', 'Eliminar noticias'),
    ('scrapers.run', 'Ejecutar scrapers')
ON CONFLICT (nombre) DO NOTHING;

-- Crear usuario admin por defecto (password: admin123 - cambiar en producción!)
-- NOTA: El hash se generará automáticamente al crear el usuario desde la API
-- O puedes usar: python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode())"
-- Para este ejemplo, usamos un hash válido de "admin123"
-- Hash bcrypt válido de "admin123": $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW
INSERT INTO usuarios (email, password_hash, nombre, apellido, rol, plan, activo, email_verificado)
VALUES ('admin@biznews.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Admin', 'Sistema', 'admin', 'enterprise', true, true)
ON CONFLICT (email) DO NOTHING;

-- Asignar todos los permisos al admin
INSERT INTO usuario_permisos (usuario_id, permiso_id, granted_by)
SELECT u.id, p.id, u.id
FROM usuarios u, permisos p
WHERE u.email = 'admin@biznews.com'
ON CONFLICT DO NOTHING;

