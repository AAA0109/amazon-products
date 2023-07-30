from apps.ads_api.entities.internal.token import Token
from apps.ads_api.mixins.auth.token_storable_mixin import TokenStorableMixin


class JWTStorableMixin(TokenStorableMixin):
    @classmethod
    def get_access_token(cls, token_id: str) -> Token:
        token_id = f"access_{token_id}"

        return cls.get_token(token_id=token_id)

    @classmethod
    def store_access_token(cls, token_id: str, value: str, token_exp_time: int):
        token_id = f"access_{token_id}"

        cls.store_token(token_id, value, token_exp_time)

    @classmethod
    def get_refresh_token(cls, token_id) -> Token:
        token_id = f"refresh_{token_id}"

        return cls.get_token(token_id=token_id)

    @classmethod
    def store_refresh_token(cls, token_id: str, value: str, token_exp_time: int):
        token_id = f"refresh_{token_id}"

        cls.store_token(token_id, value, token_exp_time)
