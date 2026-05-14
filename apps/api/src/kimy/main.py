from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kimy import __version__
from kimy.api.v1 import router as v1_router
from kimy.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "KIMY — Backend API for academic thesis review with AI evaluation, "
        "plagiarism detection (pgvector), citation validation (CrossRef), "
        "and ORCID-based advisor identity."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
    }


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": __version__,
        "docs": "/docs",
    }


app.include_router(v1_router)
