from typing import List
from fastapi import Depends, APIRouter, HTTPException, status
from pydantic import UUID4, EmailStr
from app.api.dependencies.auth import get_user_agent, get_auth_token, has_roles
from app.api.dependencies.redis_database import get_redis_repository
from app.core.config import MAXIMUN_ACTIVE_TOKENS
from app.db.repositories.token_redis import TokenRedisRepository
from app.schemas.token import AccessToken, Token
from app.schemas.security import ExtendedOAuth2PasswordRequestForm

from app.db.repositories.users import UsersRepository
from app.services import auth_service
from app.api.dependencies.database import get_repository

router = APIRouter()


@router.post("/login", response_model=AccessToken, name="auth:user-login")
async def user_login_with_email_and_password(
    get_user_agent: str = Depends(get_user_agent),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
    form_data: ExtendedOAuth2PasswordRequestForm = Depends(),
) -> AccessToken:
    user = await users_repo.authenticate_user(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication was unsuccessful.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not an active user.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unconfirmed email.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # get list of tokens with
    tokens: List[Token] = await token_redis_repo.get_tokens_by_user_id(user_id=user.id)

    # existe a limit numbers of devices to simultaneous access
    # so, is possible to remove a device
    device_remove = form_data.device_remove

    for token in tokens:
        if (device_remove and device_remove == token.device) or (token.device == get_user_agent):
            await token_redis_repo.remove_token_by_key(token.id)
            tokens.remove(token)

    if len(tokens) >= MAXIMUN_ACTIVE_TOKENS:
        devices = [t.device for t in tokens]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"You have exceeded the maximum number of devices connected simultaneously: {devices}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = await users_repo.get_redis_token_by_user(user=user, user_agent=get_user_agent)

    access_token = AccessToken(
        access_token=await auth_service.create_access_token_for_user(
            user=user, token=token, token_redis_repo=token_redis_repo
        ),
        token_type="bearer",
    )
    return access_token


@router.post("/logout", name="auth:user-logout")
async def user_logout(
    user_token: Token = Depends(get_auth_token),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
):
    await token_redis_repo.remove_tokens_by_user_id(user_id=user_token.user_id)


@router.post(
    "/force-logout-by-id/{user_id}",
    name="auth:force-user-logout-by-id",
    dependencies=[Depends(has_roles(["master", "administration"]))],
)
async def force_user_logout_by_id(
    user_id: UUID4 = None,
    user_token: Token = Depends(get_auth_token),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
):
    user = await users_repo.get_user_by_id(tenant_id=user_token.tenant_id, id=user_id)

    if user:
        await token_redis_repo.remove_tokens_by_user_id(user_id=user.id)


@router.post(
    "/force-logout-by-username/{username}",
    name="auth:force-user-logout-by-username",
    dependencies=[Depends(has_roles(["master", "administration"]))],
)
async def force_user_logout_by_username(
    username: str = None,
    user_token: Token = Depends(get_auth_token),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
):
    user = await users_repo.get_user_by_tenant_and_username(tenant_id=user_token.tenant_id, username=username)

    if user:
        await token_redis_repo.remove_tokens_by_user_id(user_id=user.id)


@router.post(
    "/force-logout-by-email/{email}",
    name="auth:force-user-logout-by-email",
    dependencies=[Depends(has_roles(["master", "administration"]))],
)
async def force_user_logout_by_email(
    email: EmailStr = None,
    user_token: Token = Depends(get_auth_token),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
    token_redis_repo: TokenRedisRepository = Depends(get_redis_repository(TokenRedisRepository)),
):
    user = await users_repo.get_user_by_tenant_id_and_email(tenant_id=user_token.tenant_id, email=email)

    if user:
        await token_redis_repo.remove_tokens_by_user_id(user_id=user.id)
