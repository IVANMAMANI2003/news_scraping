import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import close_pool, init_pool
from .routers import news

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


def _get_cors_origins() -> list[str]:
    origins_env = os.getenv("FRONTEND_ORIGINS", os.getenv("FRONTEND_ORIGIN", "http://localhost:64959/"))
    # support comma-separated list
    return [o.strip() for o in origins_env.split(",") if o.strip()]


app = FastAPI(title="News API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(news.router, prefix="/news", tags=["news"])


# Uvicorn entrypoint: uvicorn api.main:app --reload


@app.on_event("startup")
def on_startup():
    init_pool()


@app.on_event("shutdown")
def on_shutdown():
    close_pool()
