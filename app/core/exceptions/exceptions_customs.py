import http

from typing import Any, List, Optional
from pydantic import BaseModel

from app.schemas.enums import TipoKeyError


class ErrorBB(BaseModel):
    codigo: Optional[str]
    versao: Optional[str]
    mensagem: Optional[str]
    ocorrencia: Optional[str]


class ErrorBoletoBB(BaseModel):
    erros: List[ErrorBB]


class HttpExceptionBB(Exception):
    def __init__(
        self,
        status_code: int,
        detail: Optional[str] = None,
        content: Optional[Any] = None,
        headers: Optional[dict] = None,
    ) -> None:
        if detail is None:
            detail = http.HTTPStatus(status_code).phrase
        self.status_code = status_code
        self.detail = detail
        self.content = content
        self.headers = headers

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"


class KeyHttpException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: str,
        key: TipoKeyError,
        headers: Optional[dict] = None,
    ) -> None:
        if detail is None:
            detail = http.HTTPStatus(status_code).phrase
        self.status_code = status_code
        self.detail = detail
        self.key = key
        self.headers = headers

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"


class LoginHttpException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: str,
        key: TipoKeyError,
        devices: Optional[List[str]] = None,
        headers: Optional[dict] = None,
    ) -> None:
        if detail is None:
            detail = http.HTTPStatus(status_code).phrase
        self.status_code = status_code
        self.detail = detail
        self.key = key
        self.devices = devices
        self.headers = headers

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"
