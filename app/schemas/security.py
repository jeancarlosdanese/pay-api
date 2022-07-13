from typing import Optional
from fastapi import Form
from fastapi.security import OAuth2PasswordRequestForm


class ExtendedOAuth2PasswordRequestForm(OAuth2PasswordRequestForm):
    def __init__(
        self,
        grant_type: str = Form(None, regex="password"),
        username: str = Form(...),
        password: str = Form(...),
        scope: str = Form(""),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
        # extended for add device_remove
        device_remove: Optional[str] = Form(None),
    ):
        super().__init__(
            grant_type=grant_type,
            username=username,
            password=password,
            scope=scope,
            client_id=client_id,
            client_secret=client_secret,
        ),
        self.device_remove = device_remove
