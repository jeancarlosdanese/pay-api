import os
import logging
from fastapi import Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic.error_wrappers import ValidationError
from starlette.responses import JSONResponse

from asyncpg.exceptions import ForeignKeyViolationError, InvalidTextRepresentationError, UniqueViolationError

from app.core.config import DEFAULT_LOCALE, DEV_MODE
from app.core.exceptions.exceptions_customs import HttpExceptionBB, KeyHttpException, LoginHttpException

from pydantic_i18n import PydanticI18n, JsonLoader

from app.core.translator_i18n import TranslatorI18n

logger = logging.getLogger("app")

# __all__ = ["get_locale", "http422_error_handler"]


def get_locale(locale: str = DEFAULT_LOCALE) -> str:
    return locale


translations_pydantic = JsonLoader(os.path.join("app", "core", "pydantic_i18n_lang"))
tr_pydantic_i18n = PydanticI18n(translations_pydantic)
# print(PydanticI18n.get_pydantic_messages(output="json"))

translations_translator = JsonLoader(os.path.join("app", "core", "translator_i18n", "languages"))
tr_translator_i18n = TranslatorI18n(translations_translator)

# async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
#     print("METHOD: validation_exception_handler")
#     current_locale = request.query_params.get("locale", DEFAULT_LOCALE)
#     return JSONResponse(
#         status_code=HTTP_422_UNPROCESSABLE_ENTITY,
#         content={"detail": tr.translate(exc.errors(), current_locale)},
#     )


async def http422_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logging_message("METHOD: http422_error_handler")

    try:
        msgs = []
        current_locale = request.query_params.get("locale", DEFAULT_LOCALE)

        errors = tr_pydantic_i18n.translate(exc.errors(), current_locale)
        for error in errors:
            field = f"{error['loc'][1]}"
            mensagem = f"{error['msg']}"
            msgs.append({"message": f"{field}: {mensagem}"})

        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"messages": msgs})
    except Exception:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})


async def httpException_bb_error_handler(request: Request, exc: HttpExceptionBB) -> JSONResponse:
    logger.warn(f"httpException_bb_error_handler: {exc.content}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.content,
    )


async def httpException_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logging_message("METHOD: httpException_error_handler", exc)

    current_locale = request.query_params.get("locale", DEFAULT_LOCALE)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "messages": [
                {
                    "message": tr_translator_i18n.translate(exc.detail, current_locale),
                },
            ],
        },
    )


async def httpException_key_error_handler(request: Request, exc: KeyHttpException) -> JSONResponse:
    logging_message("METHOD: httpException_key_error_handler")

    current_locale = request.query_params.get("locale", DEFAULT_LOCALE)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "messages": [
                {
                    "key": exc.key,
                    "message": tr_translator_i18n.translate(exc.detail, current_locale),
                },
            ],
        },
    )


async def httpException_login_error_handler(request: Request, exc: LoginHttpException) -> JSONResponse:
    logging_message("METHOD: httpException_key_error_handler")

    current_locale = request.query_params.get("locale", DEFAULT_LOCALE)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "messages": [
                {
                    "key": exc.key,
                    "message": tr_translator_i18n.translate(exc.detail, current_locale),
                    "devices": exc.devices,
                },
            ],
        },
    )


async def validation_error_exception_handler(request: Request, exc: ValidationError):
    logging_message("METHOD: validation_error_exception_handler", exc)

    try:
        msgs = []
        current_locale = request.query_params.get("locale", DEFAULT_LOCALE)

        errors = tr_pydantic_i18n.translate(exc.errors(), current_locale)
        print(errors)
        for error in errors:
            field = f"{error['loc'][0]}"
            mensagem = f"{error['msg']}"
            msgs.append({"message": f"{field}: {mensagem}"})

        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"messages": msgs})
    except Exception:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": exc.errors()})


async def asyncpg_unique_validation_exception_handler(request: Request, exc: UniqueViolationError):
    logging_message("METHOD: asyncpg_unique_validation_exception_handler", exc)

    dict_msg = exc.as_dict()

    msg = str(dict_msg["message"]).split('"')[0].strip()

    current_locale = request.query_params.get("locale", DEFAULT_LOCALE)

    message = tr_translator_i18n.translate(msg, current_locale)

    detail = str(dict_msg["detail"]).replace("Key (", "").replace(") already exists.", "").replace(")=(", " = ")

    complement_msg = tr_translator_i18n.translate("already exists", current_locale)

    message = f'{message}: "{detail}" {complement_msg}'

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "erros": [
                {
                    "mensagem": message,
                    "detalhes": detail,
                },
            ],
        },
    )


async def asyncpg_foreignkey_validation_exception_handler(request: Request, exc: ForeignKeyViolationError):
    logging_message("METHOD: asyncpg_foreignkey_validation_exception_handler", exc)

    msg_1 = "violates foreign key constraint"
    msg_2 = "is not present in table"

    current_locale = request.query_params.get("locale", DEFAULT_LOCALE)

    msg_1 = tr_translator_i18n.translate(msg_1, current_locale)
    msg_2 = tr_translator_i18n.translate(msg_2, current_locale)

    dict_msg = exc.as_dict()
    detail = (
        str(dict_msg["detail"])
        .replace("Key (", "")
        .replace(") is not present in table", "")
        .replace(")=(", "=")
        .replace(".", "")
        .split(" ")
    )

    message = f'{msg_1}: "{detail[0].replace("=", " = ")}" {msg_2} {detail[1]}'

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "erros": [
                {
                    "mensagem": message,
                    "detalhes": detail,
                },
            ],
        },
    )


async def asyncpg_invalid_text_representation_error(request: Request, exc: InvalidTextRepresentationError):
    logging_message("METHOD: asyncpg_invalid_text_representation_error", exc)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": exc.message,
            "detail": exc.detail,
        },
    )


def logging_message(message, exc: Exception = None):
    if DEV_MODE:
        logger.warn(message)
        if exc:
            logger.error(f"type: {type(exc)} -> {exc}")
