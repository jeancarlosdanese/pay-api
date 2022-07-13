import secrets
from datetime import datetime, timedelta
from typing import Optional
from pydantic import EmailStr
from pydantic.main import BaseModel
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_AUDIENCE_AUTH


class JWTMeta(BaseModel):
    iss: Optional[str] = None
    aud: str = JWT_AUDIENCE_AUTH
    iat: float = datetime.timestamp(datetime.utcnow())
    exp: float = datetime.timestamp(datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


class JWTCreds(BaseModel):
    """How we'll identify users"""

    sub: str


class JWTCredsAuth(JWTCreds):
    """How we'll identify users"""

    email: EmailStr
    username: str


class JWTPayload(JWTMeta, JWTCreds):
    """
    JWT Payload right before it's encoded - combine meta and username
    """

    pass


class JWTPayloadAuth(JWTMeta, JWTCreds):
    """
    JWT Payload right before it's encoded - combine meta and username
    """

    pass


class AccessToken(BaseModel):
    access_token: str
    token_type: str


class ForgotPasswordToken(BaseModel):
    forgot_password_token: str


class Token(BaseModel):
    id: str = secrets.token_urlsafe(32)
    tenant_id: str
    user_id: str
    name: str = "Oauth2 Access Token"
    username: Optional[str] = ""
    email: Optional[str] = ""
    roles: Optional[str] = ""
    permissions: Optional[str] = ""
    extra_permissions: Optional[str] = ""
    device: Optional[str] = "Other"
