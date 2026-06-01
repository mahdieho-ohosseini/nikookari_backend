from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    logger.warning(
        f"HTTP error | path={request.url.path} | "
        f"method={request.method} | status_code={exc.status_code} | detail={exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "path": request.url.path,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    logger.warning(
        f"Validation error | path={request.url.path} | "
        f"method={request.method} | errors={exc.errors()}"
    )

    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Invalid request data",
            "path": request.url.path,
            "errors": exc.errors(),
        },
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        f"Unhandled server error | path={request.url.path} | "
        f"method={request.method} | error={str(exc)}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "path": request.url.path,
        },
    )