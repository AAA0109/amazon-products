import logging
from typing import Optional, Dict

import requests
from requests import Response


_logger = logging.getLogger(__name__)


class GoogleRequestService:
    def request(
        self,
        url: str,
        method: str = "GET",
    ) -> Optional[Response]:
        try:
            if method == "GET":
                response = requests.get(url)
            elif method in ["POST", "PUT"]:
                response = requests.post(url)
            else:
                raise NotImplementedError("Request method not implemented")
        except requests.exceptions.HTTPError as e:
            _logger.error("Failed to connect to Google API error: %s", e.response.text)
        else:
            return response
