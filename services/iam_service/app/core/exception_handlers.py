from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException


def make_validation_errors_json_safe(errors: list[dict]) -> list[dict]:
    safe_errors = []

    for error in errors:
        safe_error = dict(error)

        ctx = safe_error.get("ctx")
        if isinstance(ctx, dict):
            safe_error["ctx"] = {
                key: str(value)
                for key, value in ctx.items()
            }

        safe_errors.append(safe_error)

    return safe_errors


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
    safe_errors = make_validation_errors_json_safe(exc.errors())

    logger.warning(
        f"Validation error | path={request.url.path} | "
        f"method={request.method} | errors={safe_errors}"
    )

    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Invalid request data",
            "path": request.url.path,
            "errors": safe_errors,
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