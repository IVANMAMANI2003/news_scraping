import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import close_pool, init_pool
from .routers import advanced, metadata, news, social

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


app = FastAPI(title="News API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(news.router, prefix="/news", tags=["news"])
app.include_router(advanced.router, prefix="/api", tags=["advanced"])
app.include_router(metadata.router, prefix="/news", tags=["metadata"])
app.include_router(social.router, prefix="/social", tags=["social"])


# Uvicorn entrypoint: uvicorn api.main:app --reload


@app.on_event("startup")
def on_startup():
    init_pool()


@app.on_event("shutdown")
def on_shutdown():
    close_pool()
