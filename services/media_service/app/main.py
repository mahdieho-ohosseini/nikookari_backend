from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.media_routes import router as media_router
from app.core.config import get_settings
from app.core.database import create_db_and_tables, db_health_check


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Nikookari Media Service",
    lifespan=lifespan,
)


app.include_router(media_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "media_service",
        "version": settings.PROJECT_VERSION,
    }


@app.get("/health", tags=["Health"])
async def health():
    db_ok = await db_health_check()

    return {
        "status": "ok" if db_ok else "error",
        "database": db_ok,
    }


logger.success("Nikookari Media Service started successfully!")