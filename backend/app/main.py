from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import settings
from .database import engine
from .routers import (
    auth,
    crops,
    hierarchy,
    khasras,
    khatas,
    mutations,
    ownership,
    persons,
    reports,
)

app = FastAPI(
    title="Khetiyan Land Records API",
    version="1.0.0",
    description=(
        "Hindi-first land records backend for khasra, khata and mutation workflows."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (
    auth,
    hierarchy,
    persons,
    khasras,
    khatas,
    ownership,
    mutations,
    crops,
    reports,
):
    app.include_router(module.router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "name": "Khetiyan Land Records API",
        "version": app.version,
        "docs": "/docs",
    }


@app.get("/api/health", tags=["health"])
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}
