# from app.api.api_v1.reset import get_reset_password_router
from pydantic import UUID4
from app.db.repositories.tenants import TenantsRepository
from fastapi.exceptions import HTTPException

import jwt

# from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from pydantic.error_wrappers import ValidationError
from starlette.status import HTTP_401_UNAUTHORIZED
from app.db.repositories.token_redis import TokenRedisRepository
from app.schemas.tenant import TenantInDB
from app.schemas.token import JWTCreds, JWTMeta, JWTPayload, JWTPayloadAuth, Token
from app.schemas.user import UserInDB
from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES_FORGOT_PASSWORD,
    CONFIRM_EMAIL_URL,
    CONFIRM_TENANT_EMAIL_URL,
    DOMAIN_MAIN,
    HOST_MAIN,
    JWT_AUDIENCE_CONFIRM_EMAIL,
    JWT_AUDIENCE_FORGOT_PASSWORD,
    RESET_PASSWORD_URL,
    SECRET_KEY,
    JWT_ALGORITHM,
    JWT_AUDIENCE_AUTH,
    ACCESS_TOKEN_EXPIRE_MINUTES_AUTH,
)


""" pwd_context = CryptContext(
    schemes=["bcrypt"], bcrypt__default_rounds=12, bcrypt__min_rounds=8, bcrypt__max_rounds=14, deprecated="auto"
) """
pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__default_rounds=12, deprecated="auto")


class AuthException(BaseException):
    """
    Custom auth exception that can be modified later on.
    """

    pass


class AuthService:
    def create_password(self, *, plaintext_password: str) -> str:
        return self.get_password_hash(password=plaintext_password)

    def get_password_hash(self, *, password: str):
        return pwd_context.using().hash(password)

    def verify_password(self, *, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def create_access_token_for_user(
        self,
        *,
        user: UserInDB,
        token: Token,
        token_redis_repo: TokenRedisRepository,
        secret_key: str = str(SECRET_KEY),
        audience: str = JWT_AUDIENCE_AUTH,
        expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES_AUTH,
    ) -> str:
        if not user or not isinstance(user, UserInDB):
            return None

        jwt_meta = JWTMeta(
            aud=audience,
            iss=str(user.tenant_id),
            iat=datetime.timestamp(datetime.utcnow()),
            exp=datetime.timestamp(datetime.utcnow() + timedelta(minutes=expires_in)),
        )
        # jwt_creds = JWTCredsAuth(sub=str(user.id), email=user.email, username=user.username)
        jwt_creds = JWTCreds(sub=token.id)
        token_payload = JWTPayload(
            **jwt_meta.dict(),
            **jwt_creds.dict(),
        )
        # NOTE - previous versions of pyjwt ("<2.0") returned the token as bytes insted of a string.
        # That is no longer the case and the `.decode("utf-8")` has been removed.
        access_token = jwt.encode(token_payload.dict(), secret_key, algorithm=JWT_ALGORITHM)
        await token_redis_repo.set_token(token=token, expires_in=expires_in)

        return access_token

    def get_token_data_from_token(self, *, token: str, secret_key: str, audience: str) -> Optional[str]:
        try:
            decoded_token = jwt.decode(token, str(secret_key), audience=audience, algorithms=[JWT_ALGORITHM])
            payload = JWTPayloadAuth(**decoded_token)
        except (jwt.PyJWTError, ValidationError):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Could not validate token credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    async def get_url_to_forgot_password(
        self,
        *,
        tenants_repo: TenantsRepository,
        user: UserInDB,
    ) -> str:
        if not user or not isinstance(user, UserInDB):
            return None

        tenant = await tenants_repo.get_tenant_by_id(id=user.tenant_id)

        return self.get_url_token(
            path_url=str(RESET_PASSWORD_URL),
            iss=str(tenant.id),
            sub=str(user.id),
            audience=str(JWT_AUDIENCE_FORGOT_PASSWORD),
            subdomain=tenant.subdomain,
            domain=tenant.domain,
            expires_in=str(ACCESS_TOKEN_EXPIRE_MINUTES_FORGOT_PASSWORD),
        )

    async def get_url_to_tenant_email_confirm(
        self,
        *,
        sub: UUID4,
        tenant_origin: TenantInDB,
    ) -> str:
        return self.get_url_token(
            path_url=str(CONFIRM_TENANT_EMAIL_URL),
            iss=str(tenant_origin.id),
            sub=str(sub),
            subdomain=str(tenant_origin.subdomain),
            domain=str(tenant_origin.domain),
            audience=str(JWT_AUDIENCE_CONFIRM_EMAIL),
            expires_in=48 * 60,  # 48 hours
        )

    async def get_url_to_user_email_confirm(
        self,
        *,
        sub: UUID4,
        tenant_origin: TenantInDB,
    ) -> str:
        return self.get_url_token(
            path_url=str(CONFIRM_EMAIL_URL),
            iss=str(tenant_origin.id),
            sub=str(sub),
            subdomain=str(tenant_origin.subdomain),
            domain=str(tenant_origin.domain),
            audience=str(JWT_AUDIENCE_CONFIRM_EMAIL),
            expires_in=48 * 60,  # 48 hours
        )

    def get_url_token(
        self,
        *,
        path_url: str,  # ex: profile/confirm-email
        iss: str,  # ex: tenant_id
        sub: str,  # ex: user-id
        audience: str,  # ex: payapi:forgot_password
        subdomain: str = HOST_MAIN,  # ex: payapi
        domain: str = DOMAIN_MAIN,  # ex: domain.com
        expires_in: int = 2 * 60,  # 2 hours
        secret_key: str = str(SECRET_KEY),
    ) -> str:
        jwt_meta = JWTMeta(
            aud=audience,
            iss=iss,
            iat=datetime.timestamp(datetime.now()),
            exp=datetime.timestamp(datetime.now() + timedelta(minutes=int(expires_in))),
        )
        jwt_creds = JWTCreds(sub=sub)
        token_payload = JWTPayload(
            **jwt_meta.dict(),
            **jwt_creds.dict(),
        )

        token = jwt.encode(token_payload.dict(), secret_key, algorithm=JWT_ALGORITHM)
        url_token = f"https://{subdomain}.{domain}/{path_url}/{token}"

        return url_token
