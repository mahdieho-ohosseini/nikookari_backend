from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.auth_routes import auth_router
from app.api.password_routes import router as password_reset_router
from app.api.profile_routes import profile_router
from app.api.admin_routes import admin_router
from app.api.health_routes import health_router
from app.api.monitoring_routes import monitoring_router
from app.core.config import get_settings
from app.core.database import create_db_and_tables
from app.core.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.core.monitoring_middleware import RequestLoggingMiddleware
from app.logging.logging_service import configure_logger


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
# 3. Create FastAPI app
# ============================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    description="Identity and Access Management (IAM) Service for QForm",
)

logger.info(f"{settings.PROJECT_NAME} v{settings.PROJECT_VERSION} is starting up...")


# ============================================
# 4. Global Exception Handlers
# ============================================
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


# ============================================
# 5. UTF-8 Middleware
# ============================================
@app.middleware("http")
async def set_utf8_encoding(request: Request, call_next):
    response = await call_next(request)

    if isinstance(response, JSONResponse):
        response.headers["Content-Type"] = "application/json; charset=utf-8"

    return response


# ============================================
# 6. Security Scheme
# ============================================
bearer_scheme = HTTPBearer(
    auto_error=True,
    scheme_name="BearerAuth",
)


# ============================================
# 7. Custom OpenAPI
# ============================================
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="IAM Service",
        version="1.0.0",
        description="Identity and Access Management",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ============================================
# 8. Middleware
# ============================================
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

logger.info("CORS middleware configured with allow_origins: {}", origins)
logger.info("Request logging middleware enabled.")


# ============================================
# 9. Routes
# ============================================
app.include_router(auth_router, prefix="/api/v1")
logger.info("Included auth_router with prefix /api/v1")

app.include_router(password_reset_router, prefix="/api/v1")
logger.info("Included password_reset_router with prefix /api/v1")

app.include_router(profile_router, prefix="/api/v1")
logger.info("Included profile_router with prefix /api/v1")

app.include_router(admin_router, prefix="/api/v1")
logger.info("Included admin_router with prefix /api/v1")

app.include_router(health_router)
logger.info("Included health_router")

app.include_router(monitoring_router)
logger.info("Included monitoring_router")


# ============================================
# 10. Root Endpoint
# ============================================
@app.get("/", tags=["Health Check"])
async def root():
    logger.debug("Root health check endpoint was hit.")

    return {
        "status": "ok",
        "message": "Welcome to QForm IAM Service!",
    }


logger.success("🚀 IAM Service has started successfully!")