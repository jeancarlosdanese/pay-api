"""For managing validation error for complete application."""
# from typing import Union
import logging
from typing import Union
from asyncpg.exceptions import ForeignKeyViolationError, InvalidTextRepresentationError, UniqueViolationError
from fastapi.exceptions import HTTPException, RequestValidationError
from pydantic.error_wrappers import ValidationError

# from fastapi.exceptions import RequestValidationError
# from fastapi.openapi.constants import REF_PREFIX
# from fastapi.openapi.utils import validation_error_response_definition

# from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette import status

from app.core.exceptions.exceptions_customs import HttpExceptionBB

logger = logging.getLogger("app")


async def http422_error_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError],
) -> JSONResponse:
    """To handle unprocessable request(HTTP_422) and log accordingly to file.

    Args:
        _ (Request): Request object containing metadata about Request
        exc (Union[RequestValidationError, ValidationError]): to handle RequestValidationError,
            ValidationError

    Returns:
        JSONResponse: JSON response with required status code.
    """
    try:
        msgs = []
        errors = exc.errors()
        for error in errors:
            msgs.append({"message": f"{error['type']}: {error['loc'][1]} is {error['msg']}"})
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"messages": msgs})
    except Exception:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})


async def httpException_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # logger.warn(exc.detail)
    # print(f"HTTPException: {exc}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "messages": [{"message": f"value_error.missing: {exc.detail}"}],
            "detail": exc.detail,
        },
    )


async def httpException_bb_error_handler(request: Request, exc: HttpExceptionBB) -> JSONResponse:
    print(f"HttpExceptionBB: {exc.content}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.content,
    )


async def validation_error_exception_handler(request: Request, err: ValidationError):
    # print(f"ValidationError: {err}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": err,
        },
    )


async def asyncpg_unique_validation_exception_handler(request: Request, err: UniqueViolationError):
    # print(f"UniqueViolationError: {err}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "message": err.message,
            "detail": err.detail,
        },
    )


async def asyncpg_foreignkey_validation_exception_handler(request: Request, err: ForeignKeyViolationError):
    # print(f"ForeignKeyViolationError: {err}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "message": err.message,
            "detail": err.detail,
        },
    )


async def asyncpg_invalid_text_representation_error(request: Request, err: InvalidTextRepresentationError):
    # print(f"InvalidTextRepresentationError: {err}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "message": err.message,
            "detail": err.detail,
        },
    )


# validation_error_response_definition["properties"] = {
#     "errors": {
#         "title": "Errors",
#         "type": "array",
#         "items": {"$ref": "{0}ValidationError".format(REF_PREFIX)},
#     },
# }
