import logging
import logging.config
from asyncpg import InvalidTextRepresentationError
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException, RequestValidationError
from asyncpg.exceptions import ForeignKeyViolationError, UniqueViolationError
from pydantic import ValidationError

from app.core import tasks
from app.core.config import API_PREFIX_V1, PROJECT_NAME, BACKEND_CORS_ORIGINS, VERSION, WORK_MODE

from app.api.routes import router as api_router
from app.core.exceptions.exceptions_customs import HttpExceptionBB, KeyHttpException, LoginHttpException

from app.core.log_config import LogConfig

import app.core.exception_handle_translate as exp_tr

logging.config.dictConfig(LogConfig().dict())


def get_application():
    app = FastAPI(
        title=PROJECT_NAME,
        version=VERSION,
        openapi_url=None if WORK_MODE == "prod" else f"{API_PREFIX_V1}/openapi.json",
        redoc_url=None if WORK_MODE == "prod" else "/redoc",
        docs_url=None if WORK_MODE == "prod" else "/docs",
        dependencies=[Depends(exp_tr.get_locale)],
    )
    # Set all CORS enabled origins
    if BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[origin for origin in BACKEND_CORS_ORIGINS.split(",")],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_event_handler("startup", tasks.create_start_app_handler(app))
    app.add_event_handler("shutdown", tasks.create_stop_app_handler(app))

    app.add_exception_handler(RequestValidationError, exp_tr.http422_error_handler)
    app.add_exception_handler(ValidationError, exp_tr.validation_error_exception_handler)
    app.add_exception_handler(HTTPException, exp_tr.httpException_error_handler)
    app.add_exception_handler(HttpExceptionBB, exp_tr.httpException_bb_error_handler)
    app.add_exception_handler(KeyHttpException, exp_tr.httpException_key_error_handler)
    app.add_exception_handler(LoginHttpException, exp_tr.httpException_login_error_handler)
    app.add_exception_handler(UniqueViolationError, exp_tr.asyncpg_unique_validation_exception_handler)
    app.add_exception_handler(ForeignKeyViolationError, exp_tr.asyncpg_foreignkey_validation_exception_handler)
    app.add_exception_handler(InvalidTextRepresentationError, exp_tr.asyncpg_invalid_text_representation_error)

    app.include_router(api_router, prefix=API_PREFIX_V1)

    return app


app = get_application()
