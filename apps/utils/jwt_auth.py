import datetime

from functools import wraps

from apps.ads_api.entities.internal.token import Token
from apps.ads_api.exceptions.auth.token import TokenNotFoundException, TokenExpiredException
from apps.ads_api.interfaces.auth.jwt_auth_interface import JWTAuthInterface
from apps.ads_api.interfaces.auth.token_id_interface import TokenIdInterface
from apps.ads_api.mixins.auth.jwt_storable_mixin import JWTStorableMixin


class JWTAuth(JWTStorableMixin):
    @classmethod
    def auth_required(cls):
        def refresh_token_wrapper(decorated):
            @wraps(decorated)
            def wrapper(adapter_instance, *args, **kwargs):
                authenticator = adapter_instance.authenticator
                if not isinstance(authenticator, JWTAuthInterface):
                    raise NotImplementedError("Authenticator class does not implement JWTAuthInterface")
                if not isinstance(adapter_instance, TokenIdInterface):
                    raise NotImplementedError(
                        f"The TokenIdInterface interface is not implemented in the adapter class {adapter_instance}"
                    )

                token_id = adapter_instance.token_id

                try:
                    cls.check_token_expired(token_id)
                except TokenNotFoundException:
                    access_token, refresh_token, exp_time = authenticator.get_access_token()
                    cls.store_access_token(token_id, access_token, exp_time)
                    cls.store_refresh_token(token_id, access_token, exp_time + 100_000)
                except TokenExpiredException:
                    access_token, refresh_token, exp_time = authenticator.refresh_access_token()
                    cls.store_access_token(token_id, access_token, exp_time)
                    cls.store_refresh_token(token_id, access_token, exp_time + 100_000)

                access_token = cls.get_access_token(token_id)

                return decorated(adapter_instance, access_token=access_token, *args, **kwargs)

            return wrapper

        return refresh_token_wrapper

    @classmethod
    def check_token_expired(cls, token_id: str) -> bool:
        token = cls.get_access_token(token_id)

        if not cls._expired(token):
            authorized = True
        else:
            raise TokenExpiredException()

        return authorized

    @classmethod
    def _expired(cls, token: Token):
        return token.expired < datetime.datetime.now().timestamp()
