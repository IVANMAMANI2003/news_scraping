import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import close_pool, init_pool
from .routers import (admin, advanced, api_keys, auth, export, metadata, news,
                      social, users)

# Importar router de NLP cleaning
try:
    from .routers import nlp_cleaning
except ImportError as e:
    print(f"⚠️  Advertencia: No se pudo importar módulo de NLP cleaning: {e}")
    nlp_cleaning = None

# Importar scrapers después de configurar mocks de dependencias
# Esto asegura que los mocks estén disponibles antes de importar los scrapers
try:
    from .routers import scrapers
except ImportError as e:
    # Si hay error de importación, puede ser por dependencias faltantes
    print(f"⚠️  Advertencia: No se pudo importar módulo de scrapers: {e}")
    print("💡 Ejecuta: pip install beautifulsoup4 pandas requests python-dateutil")
    scrapers = None

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


def _get_cors_origins() -> list[str]:
    origins_env = os.getenv("FRONTEND_ORIGINS", os.getenv("FRONTEND_ORIGIN", ""))
    # support comma-separated list
    origins = [o.strip() for o in origins_env.split(",") if o.strip()] if origins_env else []
    # Add common local development origins
    origins.extend([
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:64959",
        "http://127.0.0.1:64959",
    ])
    # Remove duplicates while preserving order
    seen = set()
    unique_origins = []
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            unique_origins.append(origin)
    return unique_origins


app = FastAPI(title="News API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(news.router, prefix="/news", tags=["news"])
app.include_router(advanced.router, prefix="/api", tags=["advanced"])
app.include_router(metadata.router, prefix="/news", tags=["metadata"])
app.include_router(social.router, prefix="/social", tags=["social"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
app.include_router(export.router, prefix="/api", tags=["export"])

# Incluir router de NLP cleaning solo si se importó correctamente
if nlp_cleaning is not None:
    app.include_router(nlp_cleaning.router, prefix="/api", tags=["nlp-cleaning"])
else:
    print("⚠️  Router de NLP cleaning no disponible debido a dependencias faltantes")

# Incluir router de scrapers solo si se importó correctamente
if scrapers is not None:
    app.include_router(scrapers.router, prefix="/api", tags=["scrapers"])
else:
    print("⚠️  Router de scrapers no disponible debido a dependencias faltantes")


# Uvicorn entrypoint: uvicorn api.main:app --reload


@app.on_event("startup")
def on_startup():
    init_pool()


@app.on_event("shutdown")
def on_shutdown():
    close_pool()
