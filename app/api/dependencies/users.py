from fastapi import HTTPException, Depends, Path, status
from pydantic.types import UUID4
from app.schemas.token import Token

from app.schemas.user import UserInDB

from app.db.repositories.users import UsersRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_auth_token


async def get_user_by_id_from_path(
    id: UUID4 = Path(..., title="The ID of the user to get."),
    user_token: Token = Depends(get_auth_token),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserInDB:
    user = await users_repo.get_user_by_id(tenant_id=user_token.tenant_id, id=id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with that id.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not an active user.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_user_by_username_from_path(
    username: str = Path(..., min_length=3, max_length=70, regex="^[a-zA-Z0-9_-]+$"),
    user_token: Token = Depends(get_auth_token),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> UserInDB:
    user = await users_repo.get_user_by_username(username=username, populate=False)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with that username.",
        )
    return user
