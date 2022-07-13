from pydantic.main import BaseModel


class AccessTokenBB(BaseModel):
    id: str
    access_token: str
    token_type: str
    expires_in: int


class TokenBB(AccessTokenBB):
    pass
