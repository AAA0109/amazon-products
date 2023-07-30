import datetime
from unittest.mock import MagicMock

import mock
import pytest
from mock.mock import Mock

from apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter import BaseAmazonAdsAdapter
from apps.ads_api.constants import ServerLocation
from apps.ads_api.entities.internal.token import Token
from apps.ads_api.exceptions.auth.token import TokenExpiredException, AuthFailed
from apps.utils.jwt_auth import JWTAuth


class TestJWTAuth:
    def test_token_not_expired(self, monkeypatch):
        token_id = "my_access_token_id"
        token = Token(value="my_token_value",
                      expired=(datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())
        get_access_token_mock = MagicMock(return_value=token)
        monkeypatch.setattr(JWTAuth, "get_access_token", get_access_token_mock)

        authorized = JWTAuth.check_token_expired(token_id)

        assert authorized is True

    def test_token_expired(self, monkeypatch):
        token_id = "my_expired_access_token_id"
        token = Token(value="my_token_value",
                      expired=(datetime.datetime.now() - datetime.timedelta(days=1)).timestamp())
        get_access_token_mock = MagicMock(return_value=token)
        monkeypatch.setattr(JWTAuth, "get_access_token", get_access_token_mock)

        with pytest.raises(TokenExpiredException):
            JWTAuth.check_token_expired(token_id)

    @mock.patch("apps.ads_api.mixins.auth.jwt_storable_mixin.JWTStorableMixin.get_access_token")
    @mock.patch("apps.utils.jwt_auth.JWTAuth.check_token_expired")
    @mock.patch("apps.ads_api.authenticators.amazon_ads_authentificator.AmazonAuthenticator._auth")
    @mock.patch("requests.sessions.Session.get")
    @mock.patch("time.sleep")
    def test_send_request_sould_be_called_5_times_and_then_failed(
            self,
            sleep_mock: Mock,
            get_mock: Mock,
            auth_mock: Mock,
            check_token_expired_mock: Mock,
            get_access_token_mock: Mock,
    ):
        get_mock.side_effect = AuthFailed
        auth_mock.return_value = ("access_token", "refresh_token", 12312312)
        check_token_expired_mock.return_value = False
        get_access_token_mock.return_value = Mock(value="access_token")
        adapter = BaseAmazonAdsAdapter(ServerLocation.EUROPE)

        with pytest.raises(AuthFailed):
            adapter.send_request(url="http://some/test/url", method="GET")

        assert get_mock.call_count == 5

    @mock.patch("apps.ads_api.mixins.auth.jwt_storable_mixin.JWTStorableMixin.get_access_token")
    @mock.patch("apps.utils.jwt_auth.JWTAuth.check_token_expired")
    @mock.patch("apps.ads_api.authenticators.amazon_ads_authentificator.AmazonAuthenticator._auth")
    @mock.patch("requests.sessions.Session.get")
    @mock.patch("time.sleep")
    def test_response_returned_after_failed_auth_condition(
            self,
            sleep_mock: Mock,
            get_mock: Mock,
            auth_mock: Mock,
            check_token_expired_mock: Mock,
            get_access_token_mock: Mock,
    ):
        get_mock.side_effect = [AuthFailed, Mock(json=lambda: {"response_ok": True})]
        auth_mock.return_value = ("access_token", "refresh_token", 12312312)
        check_token_expired_mock.return_value = False
        get_access_token_mock.return_value = Mock(value="access_token")
        adapter = BaseAmazonAdsAdapter(ServerLocation.EUROPE)

        response = adapter.send_request(url="http://some/test/url", method="GET")
        assert response.json() == {"response_ok": True}
