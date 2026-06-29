from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.media_routes import router as media_router
from app.api.monitoring_router import monitoring_router
from app.core.config import get_settings
from app.core.database import create_db_and_tables, db_health_check
from app.core.exception_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.monitoring_middleware import RequestLoggingMiddleware
from app.logging.logging_service import configure_logger


configure_logger()
logger.info("Logger configured.")

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


app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)
app.add_exception_handler(
    Exception,
    unhandled_exception_handler,
)
logger.info("Global exception handlers registered.")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS middleware configured.")


app.add_middleware(RequestLoggingMiddleware)
logger.info("Request logging middleware enabled.")


@app.middleware("http")
async def set_utf8_encoding(request: Request, call_next):
    response = await call_next(request)
    if isinstance(response, JSONResponse):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


app.include_router(media_router)
app.include_router(monitoring_router)


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


@app.get("/health/details", tags=["Health"])
async def health_details():
    db_ok = await db_health_check()

    return {
        "status": "ok" if db_ok else "error",
        "service": "media-service",
        "version": settings.PROJECT_VERSION,
        "database": db_ok,
        "storage": {
            "backend": settings.STORAGE_BACKEND,
            "upload_dir": settings.UPLOAD_DIR,
        },
    }


logger.success("Nikookari Media Service started successfully!")