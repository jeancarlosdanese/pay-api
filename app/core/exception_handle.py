"""For managing validation error for complete application."""
import logging
from typing import Union
from asyncpg.exceptions import ForeignKeyViolationError, InvalidTextRepresentationError, UniqueViolationError
from fastapi.exceptions import HTTPException, RequestValidationError
from pydantic.error_wrappers import ValidationError


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
    logger.warn(f"http422_error_handler: {exc}")
    """To handle unprocessable request(HTTP_422) and log accordingly to file.

    Args:
        _ (Request): Request object containing metadata about Request
        exc (Union[RequestValidationError, ValidationError]): to handle RequestValidationError,
            ValidationError

    Returns:
        JSONResponse: JSON response with required status code.
    """
    print(exc)
    try:
        msgs = []
        errors = exc.errors()
        for error in errors:
            msgs.append({"message": f"{error['type']}: {error['loc'][1]} is {error['msg']}"})
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"messages": msgs})
    except Exception:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})


async def httpException_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.warn(f"httpException_error_handler: {exc}")
    # logger.warn(exc.detail)
    # print(f"HTTPException: {exc}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "erros": [
                {
                    "mensagem": exc.detail,
                    "detail": f"value_error.missing: {exc.detail}",
                }
            ]
        },
    )


# {
# 	"erros": [
# 		{
# 			"codigo": "4874915",
# 			"versao": "1",
# 			"mensagem": "Nosso Número já incluído anteriormente.",
# 			"ocorrencia": "DCsBWK/o2FSyLoUlNAHc0101"
# 		}
# 	]
# }


async def httpException_bb_error_handler(request: Request, exc: HttpExceptionBB) -> JSONResponse:
    logger.warn(f"httpException_bb_error_handler: {exc.content}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.content,
    )


async def validation_error_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    logger.warn(f"validation_error_exception_handler: {exc}")
    # print(f"ValidationError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "erros": [
                {
                    "mensagem": exc.message,
                    "detalhes": exc.detail,
                }
            ]
        },
    )


async def asyncpg_unique_validation_exception_handler(request: Request, exc: UniqueViolationError) -> JSONResponse:
    logger.warn(f"asyncpg_unique_validation_exception_handler: {exc}")
    # print(f"UniqueViolationError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "erros": [
                {
                    "mensagem": exc.message,
                    "detalhes": exc.detail,
                }
            ]
        },
    )


async def asyncpg_foreignkey_validation_exception_handler(
    request: Request, exc: ForeignKeyViolationError
) -> JSONResponse:
    logger.warn(f"asyncpg_foreignkey_validation_exception_handler: {exc}")
    # print(f"ForeignKeyViolationError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "erros": [
                {
                    "mensagem": exc.message,
                    "detalhes": exc.detail,
                }
            ]
        },
    )


async def asyncpg_invalid_text_representation_error(
    request: Request, exc: InvalidTextRepresentationError
) -> JSONResponse:
    logger.warn(f"asyncpg_invalid_text_representation_error: {exc}")
    # print(f"InvalidTextRepresentationError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "erros": [
                {
                    "mensagem": exc.message,
                    "detalhes": exc.detail,
                }
            ]
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.warn(f"generic_exception_handler: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "erros": [
                {
                    "mensagem": exc.message,
                    "detalhes": exc.detail,
                }
            ]
        },
    )


# {
# 	"erros": [
# 		{
# 			"codigo": "4874915",
# 			"versao": "1",
# 			"mensagem": "Nosso Número já incluído anteriormente.",
# 			"ocorrencia": "DCsBWK/o2FSyLoUlNAHc0101"
# 		}
# 	]
# }

# {
# 	"status": "error",
# 	"message": "duplicate key value violates unique constraint \
#       "boletos_bb_convenio_bancario_id_and_numero_titulo_benef_a2ea\"",
# 	"detail": "Key (convenio_bancario_id, numero_titulo_beneficiario)=(b9b2245f-d6d8-4d66-95c7-78b8dedcce69,
#       12344245) already exists."
# }

# {
# 	"erros": [
# 		{
# 			"status": "error",
# 			"message": "duplicate key value violates unique constraint \
#               "boletos_bb_convenio_bancario_id_and_numero_titulo_benef_a2ea\"",
# 			"detail": "Key (convenio_bancario_id, numero_titulo_beneficiario)=(b9b2245f-d6d8-4d66-95c7-78b8dedcce69,
#       12344245) already exists."
# 		}
# 	]
# }
