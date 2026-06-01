from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
from loguru import logger

from app.api.form_routes import router as forms_router
from app.api.question_routes import router as question_router
from app.api.setting_routes import router as setting_router
from app.api.send_public_link_routes import router as url_router
from app.api.public_response_routes import router as public_response
from app.api.report_routes import router as report
from app.api.public_form_routes import router as public_form
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
# 3. Create FastAPI App (ONLY ONCE)
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
# 4. CORS (MUST be first)
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
# 6. UTF‑8 Middleware
# ============================================
@app.middleware("http")
async def set_utf8_encoding(request: Request, call_next):
    response = await call_next(request)
    if isinstance(response, JSONResponse):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response

# ============================================
# 7. Swagger JWT Config
# ============================================
bearer_scheme = HTTPBearer(auto_error=True)

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
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
logger.info("✅ OpenAPI configured")

# ============================================
# 8. Routes
# ============================================
app.include_router(forms_router, prefix="/api/v1")
app.include_router(question_router, prefix="/api/v1")
app.include_router(setting_router, prefix="/api/v1")
app.include_router(url_router, prefix="/api/v1")
app.include_router(public_response)
app.include_router(report, prefix="/api/v1")
app.include_router(public_form, prefix="/api/v1")


# ============================================
# 9. Health
# ============================================
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "QForm Core",
        "version": settings.PROJECT_VERSION,
    }

logger.success("🚀 QForm CORE Service started successfully!")
