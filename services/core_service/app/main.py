from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.RegInstitute_routes import router as RegInstitute
from app.api.campaign_report_router import router as campaign_report_router
from app.api.campaign_router import router as campaign_router
from app.api.charity_profile_router import router as charity_profile_router
from app.api.contribution_router import router as contribution_router
from app.api.notification_router import router as notification_router
from app.api.public_charity_router import router as public_charity_router
from app.api.verifier_router import router as verifier_router
from app.core.config import get_settings
from app.core.database import create_db_and_tables
from app.logging.logging_service import configure_logger
from app.services.jwt_middleware import jwt_middleware
from app.api.skill_document_router import router as skill_document_router


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
    description="QForm Core Service",
    lifespan=lifespan,
)

logger.info(f"{settings.PROJECT_NAME} v{settings.PROJECT_VERSION} is starting up...")


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
logger.info("✅ CORS middleware configured")


app.middleware("http")(jwt_middleware)
logger.info("✅ JWT middleware attached")


@app.middleware("http")
async def set_utf8_encoding(request: Request, call_next):
    response = await call_next(request)
    if isinstance(response, JSONResponse):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


app.include_router(RegInstitute, prefix="/api/v1")
app.include_router(verifier_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(charity_profile_router, prefix="/api/v1")
app.include_router(public_charity_router, prefix="/api/v1")
app.include_router(campaign_router, prefix="/api/v1")
app.include_router(contribution_router, prefix="/api/v1")
app.include_router(campaign_report_router, prefix="/api/v1")
app.include_router(skill_document_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "QForm Core",
        "version": settings.PROJECT_VERSION,
    }


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "service": "core-service",
        "version": settings.PROJECT_VERSION,
    }


PUBLIC_OPENAPI_PATHS = (
    "/",
    "/health",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/verify-otp",
    "/api/v1/auth/refresh",
    "/api/v1/charities",
    "/api/v1/payments/mock",
    "/api/v1/payments/callback",
)


def is_public_openapi_path(path: str) -> bool:
    return any(
        path == public_path or path.startswith(f"{public_path}/")
        for public_path in PUBLIC_OPENAPI_PATHS
    )


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description="JWT-protected Core APIs",
        routes=app.routes,
    )

    openapi_schema.setdefault("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    openapi_schema["security"] = [{"BearerAuth": []}]

    for path, path_config in openapi_schema.get("paths", {}).items():
        if is_public_openapi_path(path):
            for operation in path_config.values():
                operation["security"] = []

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
logger.info("✅ OpenAPI configured")

logger.success("🚀 QForm CORE Service started successfully!")