import base64
import aiohttp
import ssl
from fastapi import status

from app.core.config import BB_OAUTH_URL
from app.db.repositories.token_bb_redis import TokenBBRedisRepository
from app.schemas.token_bb import TokenBB


class AuthServiceBB:
    async def get_access_token_bb(
        self,
        *,
        grant_type: str = "client_credentials",
        client_id: str,
        client_secret: str,
        gw_dev_app_key: str,
        token_bb_redis_repo: TokenBBRedisRepository,
    ) -> TokenBB:
        token = await token_bb_redis_repo.get_token_by_id(id=gw_dev_app_key)

        if token:
            return token

        # basic_encoded = base64.b64encode(bytes(f"{client_id}:{client_secret}", "utf-8"))
        basic_encoded = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
        headers = {
            "Authorization": f"Basic {basic_encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        params = {
            "gw-dev-app-key": gw_dev_app_key,
        }

        data = {"grant_type": grant_type, "client_id": client_id, "client_secret": client_secret}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                url=f"{BB_OAUTH_URL}/token", params=params, ssl=ssl.SSLContext(), data=data
            ) as response:
                if response.status == status.HTTP_201_CREATED:
                    result = await response.json()
                    token = TokenBB(id=gw_dev_app_key, **result)
                    await token_bb_redis_repo.set_token(token=token, expires_in=token.expires_in - 10)
                    return token
