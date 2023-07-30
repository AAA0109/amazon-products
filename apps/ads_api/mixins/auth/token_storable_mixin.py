import datetime

from django.core.cache import cache

from apps.ads_api.entities.internal.token import Token
from apps.ads_api.exceptions.auth.token import TokenNotFoundException


class TokenStorableMixin:
    @staticmethod
    def get_token(token_id: str) -> Token:
        """
        Returns access token or raises TokenNotFoundException()
        """
        token = cache.get(token_id)
        if not token:
            raise TokenNotFoundException()

        token = Token(**token)
        return token

    @staticmethod
    def store_token(token_id: str, value: str, token_exp_time: int):
        timeout = token_exp_time - datetime.datetime.now().timestamp()
        cache.add(
            key=token_id,
            value={"value": value, "expired": token_exp_time},
            timeout=timeout,
        )
