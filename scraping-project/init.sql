-- Script de inicialización para AWS
CREATE TABLE IF NOT EXISTS noticias (
    id SERIAL PRIMARY KEY,
    titulo TEXT,
    fecha TIMESTAMP,
    hora TIME,
    resumen TEXT,
    contenido TEXT,
    categoria VARCHAR(100),
    autor VARCHAR(200),
    tags TEXT,
    url TEXT UNIQUE,
    fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    imagenes TEXT,
    fuente VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_noticias_fuente ON noticias(fuente);
CREATE INDEX IF NOT EXISTS idx_noticias_fecha ON noticias(fecha);
CREATE INDEX IF NOT EXISTS idx_noticias_url ON noticias(url);

-- Tabla de control de scraping
CREATE TABLE IF NOT EXISTS scraping_control (
    id SERIAL PRIMARY KEY,
    fuente VARCHAR(100) NOT NULL,
    ultima_pagina INTEGER DEFAULT 0,
    ultima_ejecucion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(50) DEFAULT 'activo',
    total_noticias INTEGER DEFAULT 0
);

-- Insertar fuentes de noticias
INSERT INTO scraping_control (fuente, ultima_pagina, estado) VALUES
('Pachamama Radio', 0, 'activo'),
('Puno Noticias', 0, 'activo'),
('Sin Fronteras', 0, 'activo'),
('Los Andes', 0, 'activo')
ON CONFLICT (fuente) DO NOTHING;
