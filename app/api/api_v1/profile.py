import base64
from fastapi import UploadFile, File, HTTPException
from starlette.background import BackgroundTasks
from starlette.responses import FileResponse
from app.api.dependencies.redis_database import get_redis_repository
from app.db.repositories.token_redis import TokenRedisRepository
from app.schemas.tenant import TenantInDB
from app.schemas.token import JWTPayloadAuth, Token
from app.services.send_email import send_email_in_background_with_template
from typing import Any, Optional
from starlette import status
from pydantic.networks import EmailStr

from app.api.dependencies.profile import (
    get_user_by_forgot_password_token_from_path,
)
from app.api.dependencies.database import get_repository
from app.db.repositories.users import UsersRepository
from app.db.repositories.tenants import TenantsRepository
from app.services import auth_service

from fastapi import Depends, APIRouter, Form, Body
from app.schemas.user import UserFull, UserInDB, UserPublic, UserResetPassword

from app.api.dependencies.auth import get_tenant_by_api_key, get_user_from_confirm_email_token, get_auth_token


router = APIRouter()


@router.get("/me", response_model=UserPublic, name="profile:get-current-user")
async def get_currently_authenticated_user(
    user_token: Token = Depends(get_auth_token),
    user_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    return await user_repo.get_user_by_id(tenant_id=user_token.tenant_id, id=user_token.user_id)


@router.post("/forgot-password", response_model=Any, name="auth:forgot-password")
async def forgot_password(
    background_tasks: BackgroundTasks,
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
    tenantes_repo: TenantsRepository = Depends(get_repository(TenantsRepository)),
    email: EmailStr = Form(...),
) -> Any:
    user = await users_repo.get_user_by_email(email=email)

    if user:
        url_forgot_password_token = await auth_service.get_url_to_forgot_password(tenants_repo=tenantes_repo, user=user)

        # remove all tokens from user
        await token_redis_repo.remove_tokens_by_user_id(user_id=user.id)

        if url_forgot_password_token:
            send_email_in_background_with_template(
                background_tasks,
                "Forgot password",
                email,
                {"url": url_forgot_password_token, "name": user.full_name.upper()},
                "forgot-password.html",
            )

    return {"message": "email to reset password sended with success."}


@router.post("/reset-password/{forgot_password_token}", response_model=Any, name="auth:reset-password")
async def reset_password(
    user: UserInDB = Depends(get_user_by_forgot_password_token_from_path),
    user_reset_password: UserResetPassword = Body(..., embed=False),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> Any:
    if user_reset_password.password != user_reset_password.password_confirmation:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="password and password_confirmation do not match.",
        )

    user = await users_repo.update_password(tenant_id=user.tenant_id, id=user.id, password=user_reset_password.password)
    return user


@router.post("/confirm-email/{confirm_email_token}", response_model=Optional[UserPublic], name="auth:confirm-email")
async def confirm_email(
    payload: JWTPayloadAuth = Depends(get_user_from_confirm_email_token),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> Optional[UserPublic]:
    return await users_repo.confirm_email(tenant_id=str(payload.iss), user_id=str(payload.sub))


@router.post("/upload-thumbnail", name="profile:upload-thumbnail")
async def upload_thumbnail(
    user_token: Token = Depends(get_auth_token),
    file: UploadFile = File(...),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserPublic:
    current_user = await users_repo.get_user_by_id(tenant_id=user_token.tenant_id, id=user_token.user_id)
    if not file or file.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="file type must be JPG or PNG type.",
        )

    user_updated = await users_repo.update_thumbnail(user=current_user, file=file)

    return user_updated


@router.get("/me/full", response_model=UserFull, name="profile:get-full-current-user")
async def get_full_current_user(
    user_token: Token = Depends(get_auth_token),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserFull:
    current_user = await users_repo.get_user_by_id(tenant_id=user_token.tenant_id, id=user_token.user_id)
    return await users_repo.get_full_user_by_user(user=current_user)


@router.get("/me/thumbnail")
async def download_thumbnail(
    user_token: Token = Depends(get_auth_token),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
):
    current_user = await users_repo.get_user_by_id(tenant_id=user_token.tenant_id, id=user_token.user_id)
    if current_user.thumbnail:
        return FileResponse(f"uploads/profiles/{current_user.thumbnail}")

    return None


@router.get("/me/thumbnail/base-64")
async def download_thumbnail_base_64(
    user_token: Token = Depends(get_auth_token),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
):
    current_user = await users_repo.get_user_by_id(tenant_id=user_token.tenant_id, id=user_token.user_id)
    if current_user.thumbnail:
        with open(f"uploads/profiles/{current_user.thumbnail}", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())

        return encoded_string

    return None


@router.get(
    "/me/thumbnail/s3",
    name="orders:s3-url-photos-by-id",
)
async def get_s3_url_thumbnail_s3(
    user_token: Token = Depends(get_auth_token),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
):
    current_user = await users_repo.get_user_by_id(tenant_id=user_token.tenant_id, id=user_token.user_id)
    if current_user.thumbnail:
        url_s3 = await users_repo.get_s3_url_thumbnail_s3(filename=current_user.thumbnail)

        return url_s3

    return None


@router.post(
    "/{email}/send-email-verification",
    name="profile:send-email-verification",
)
async def send_email_verification(
    background_tasks: BackgroundTasks,
    email: EmailStr,
    tenant_origin: TenantInDB = Depends(get_tenant_by_api_key),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> None:
    if not tenant_origin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not authorized for this Tenant.",
        )

    user = await users_repo.get_user_by_tenant_id_and_email(tenant_id=tenant_origin.id, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not authorized for this User.",
        )

    url_confirm_email = await auth_service.get_url_to_user_email_confirm(sub=user.id, tenant_origin=tenant_origin)
    send_email_in_background_with_template(
        background_tasks,
        f"Bem vindo à {tenant_origin.name}",
        user.email,
        {"name": user.full_name.upper(), "url": url_confirm_email},
        "welcome.html",
    )
