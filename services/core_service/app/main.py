from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.RegInstitute_routes import router as RegInstitute
from app.api.charity_profile_router import router as charity_profile_router
from app.api.notification_router import router as notification_router
from app.api.public_charity_router import router as public_charity_router
from app.api.verifier_router import router as verifier_router
from app.core.config import get_settings
from app.core.database import create_db_and_tables
from app.logging.logging_service import configure_logger
from app.services.jwt_middleware import jwt_middleware


# ============================================
# 1. Logger
# ============================================
configure_logger()
logger.info("Logger configured.")

settings = get_settings()


# ============================================
# 2. Lifespan
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


# ============================================
# 3. Create FastAPI App
# ============================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="QForm Core Service",
    lifespan=lifespan,
)

logger.info(
    f"{settings.PROJECT_NAME} v{settings.PROJECT_VERSION} is starting up..."
)


# ============================================
# 4. CORS
# ============================================
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


# ============================================
# 5. JWT Middleware
# ============================================
app.middleware("http")(jwt_middleware)
logger.info("✅ JWT middleware attached")


# ============================================
# 6. UTF-8 Middleware
# ============================================
@app.middleware("http")
async def set_utf8_encoding(request: Request, call_next):
    response = await call_next(request)
    if isinstance(response, JSONResponse):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


# ============================================
# 7. Routes
# ============================================
app.include_router(RegInstitute, prefix="/api/v1")
app.include_router(verifier_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(charity_profile_router, prefix="/api/v1")
app.include_router(public_charity_router, prefix="/api/v1")


# ============================================
# 8. Health
# ============================================
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "QForm Core",
        "version": settings.PROJECT_VERSION,
    }


# ============================================
# 9. Swagger JWT Config
# ============================================
PUBLIC_OPENAPI_PATHS = (
    "/",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/verify-otp",
    "/api/v1/auth/refresh",
    "/api/v1/charities",
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

    # By default, APIs are protected with Bearer token.
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Public APIs should not show the lock icon in Swagger.
    for path, path_config in openapi_schema.get("paths", {}).items():
        if is_public_openapi_path(path):
            for operation in path_config.values():
                operation["security"] = []

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
logger.info("✅ OpenAPI configured")

logger.success("🚀 QForm CORE Service started successfully!")
