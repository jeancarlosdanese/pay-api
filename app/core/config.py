import secrets

from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

PROJECT_NAME: str = "pay-api"
VERSION: str = "1.0.6"
API_PREFIX_V1: str = "/api/v1"
WORK_MODE: str = config("WORK_MODE", cast=str, default="prod")

BACKEND_CORS_ORIGINS: str = config("BACKEND_CORS_ORIGINS", default=["http://localhost"])

HOST_MAIN: str = config("HOST_MAIN", cast=str, default="pay")
DOMAIN_MAIN: str = config("DOMAIN_MAIN", cast=str, default="hyberica.io")
EMAIL_MAIN: str = config("EMAIL_MAIN", cast=str, default="master@hyberica.io")

# SECRET_KEY: str = secrets.token_urlsafe(32)
SECRET_KEY: str = config("SECRET_KEY", cast=Secret, default=secrets.token_urlsafe(72))

ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", cast=int, default=30)  # 30 minutes
ACCESS_TOKEN_EXPIRE_MINUTES_AUTH = config("ACCESS_TOKEN_EXPIRE_MINUTES_AUTH", cast=int, default=7 * 24 * 60)  # one week
ACCESS_TOKEN_EXPIRE_MINUTES_FORGOT_PASSWORD = config(
    "ACCESS_TOKEN_EXPIRE_MINUTES_FORGOT_PASSWORD",
    cast=int,
    default=2 * 60,  # 2 hours
)

# limit numbers of devices to simultaneous access
MAXIMUN_ACTIVE_TOKENS = config("MAXIMUN_ACTIVE_TOKENS", cast=int, default=3)  # 3 active tokens

JWT_ALGORITHM: str = "HS256"
JWT_AUDIENCE_AUTH: str = "payapi:auth"
JWT_AUDIENCE_FORGOT_PASSWORD: str = "payapi:forgot_password"
JWT_AUDIENCE_CONFIRM_EMAIL: str = "payapi:confirm_email"
JWT_TOKEN_PREFIX_AUTH: str = "Bearer"

RESET_PASSWORD_URL: str = "profile/reset-password"
CONFIRM_EMAIL_URL: str = "profile/confirm-email"
CONFIRM_TENANT_EMAIL_URL: str = "tenants/confirm-email"

POSTGRES_SERVER: str = config("POSTGRES_SERVER", cast=str, default="db")
POSTGRES_USER: str = config("POSTGRES_USER", cast=str)
POSTGRES_PASSWORD: str = config("POSTGRES_PASSWORD", cast=Secret)
POSTGRES_DB: str = config("POSTGRES_DB", cast=str)
POSTGRES_PORT: str = config("POSTGRES_PORT", cast=str, default="5432")

DATABASE_URL = config(
    "DATABASE_URL",
    cast=DatabaseURL,
    default=f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}",
)

MAIL_USERNAME: str = config("MAIL_USERNAME")
MAIL_PASSWORD: str = config("MAIL_PASSWORD")
MAIL_FROM: str = config("MAIL_FROM", default="noreplay@domain.com")
MAIL_PORT: int = config("MAIL_PORT", cast=int, default=587)
MAIL_SERVER: str = config("MAIL_SERVER")
MAIL_FROM_NAME: str = config("MAIN_FROM_NAME", default="Your Company")

REDIS_HOST: str = config("REDIS_HOST", default="localhost")
REDIS_PORT: int = config("REDIS_PORT", default=6379)
REDIS_DB: int = config("REDIS_DB", default=3)
REDIS_PREFIX: str = config("REDIS_PREFIX", default="pay_api")

S3_BUCKET: str = config("S3_BUCKET", default="hy-tests")
S3_EXPIRES_IN: str = config("S3_EXPIRES_IN", default=60)

BB_OAUTH_URL: str = config("BB_OAUTH_URL", default="https://oauth.sandbox.bb.com.br/oauth")
BB_API_URL: str = config("BB_API_URL", default="https://api.sandbox.bb.com.br/cobrancas/v2")
