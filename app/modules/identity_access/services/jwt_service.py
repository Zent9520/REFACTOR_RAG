from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jwt

from app.core.settings import settings


class JwtService:

    @staticmethod
    def create_access_token(
        user_id: str,
        email: str,
    ) -> str:

        now = datetime.now(timezone.utc)

        payload = {
            "sub": user_id,
            "email": email,
            "iat": now,
            "exp": now + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            ),
        }

        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    @staticmethod
    def decode_access_token(
        token: str,
    ) -> dict:

        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[
                settings.ALGORITHM,
            ],
        )