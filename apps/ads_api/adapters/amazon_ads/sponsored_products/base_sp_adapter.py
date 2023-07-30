import logging
from typing import List, Optional, Type, Union

from pydantic import BaseModel, parse_obj_as
from requests import Response

from apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter import (
    BaseAmazonAdsAdapter,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.search_filters import (
    AdGroupSearchFilter,
    CampaignNegativeKeywordSearchFilter,
    CampaignNegativeTargetSearchFilter,
    CampaignSearchFilter,
    KeywordSearchFilter,
    NegativeKeywordSearchFilter,
    NegativeTargetSearchFilter,
    ProductAdSearchFilter,
    TargetSearchFilter,
)
from apps.ads_api.exceptions.ads_api.base import (
    ObjectNotCreatedError,
    ObjectNotUpdatedError,
)
from apps.ads_api.models import Profile
from apps.utils.chunks import chunker

_logger = logging.getLogger(__name__)


class BaseSponsoredProductsAdapter(BaseAmazonAdsAdapter):
    HEADERS: dict
    URL: str
    ENTITY: Type[BaseModel]
    RESPONSE_DATA_KEY: str
    RESPONSE_DATA_ID: str

    def __init__(self, profile: Profile):
        super().__init__(profile.profile_server)
        self.HEADERS.update(
            {
                "Amazon-Advertising-API-Scope": str(profile.profile_id),
            }
        )
        self.validate_all_data_provided()

    def create(self, object: dict) -> str:
        success, errors = self._bulk_create_or_update([object], "POST")
        if errors:
            _logger.error(f"Object not created. Details {errors}")
            raise ObjectNotCreatedError(errors)
        return success[0]

    def batch_create(self, objects: list[dict]):
        return self._bulk_create_or_update(objects, "POST")

    def update(self, object: dict) -> str:
        success, errors = self._bulk_create_or_update([object], "PUT")
        if errors:
            _logger.error(f"Object not updated. Details {errors}")
            raise ObjectNotUpdatedError(f"Object not updated. Details {errors}")
        return success[0]

    def batch_update(self, objects: list[dict]):
        return self._bulk_create_or_update(objects, "PUT")

    def list(
        self,
        search_filter: Optional[
            Union[
                CampaignSearchFilter,
                ProductAdSearchFilter,
                AdGroupSearchFilter,
                KeywordSearchFilter,
                TargetSearchFilter,
                NegativeKeywordSearchFilter,
                CampaignNegativeKeywordSearchFilter,
                NegativeTargetSearchFilter,
                CampaignNegativeTargetSearchFilter,
            ]
        ] = None,
    ):
        body = {}
        next_token = True
        objects = []
        if search_filter:
            body = search_filter.dict(exclude_none=True, by_alias=True)
        while next_token:
            if next_token and isinstance(next_token, str):
                body["nextToken"] = next_token

            response = self.send_request(
                url=f"{self.URL}/list",
                method="POST",
                extra_headers=self.HEADERS,
                body=body,
            )

            if response is None:
                _logger.error(
                    "No response received from %s. Headers: %s, Entity: %s",
                    self.URL,
                    self.HEADERS,
                    self.ENTITY,
                )
                continue

            if response.status_code != 200:
                _logger.error(
                    "Request to %s was not successful. Details: %s",
                    self.URL,
                    response.json(),
                )
                continue

            objects += parse_obj_as(list[self.ENTITY], response.json()[self.RESPONSE_DATA_KEY])
            next_token = response.json().get("nextToken")

        return objects

    def delete(
        self,
        search_filter: Union[
            CampaignSearchFilter,
            ProductAdSearchFilter,
            AdGroupSearchFilter,
            KeywordSearchFilter,
            TargetSearchFilter,
            NegativeKeywordSearchFilter,
            CampaignNegativeKeywordSearchFilter,
            NegativeTargetSearchFilter,
            CampaignNegativeTargetSearchFilter,
        ],
    ) -> tuple[List[str], List[str]]:
        """
        Requeired for IdFilter included

        Args:
            search_filter (Union[ CampaignSearchFilter, ProductAdSearchFilter, AdGroupSearchFilter, KeywordSearchFilter, TargetSearchFilter, NegativeKeywordSearchFilter, CampaignNegativeKeywordSearchFilter, NegativeTargetSearchFilter, CampaignNegativeTargetSearchFilter, ])

        Returns:
            A tuple containing two lists: the first is a list of IDs for successfully deleted objects, the second is a list of error messages for objects that could not be deleted.
        """
        body = search_filter.dict(exclude_none=True, by_alias=True)
        response = self.send_request(
            url=f"{self.URL}/delete",
            body=body,
            extra_headers=self.HEADERS,
            method="POST",
        )
        success, errors = self._parse_response(response)
        return success, errors

    @classmethod
    def _parse_response(cls, response: Response) -> tuple[List[str], List[str]]:
        response_data = response.json()
        objects_success: list[str] = [
            camp[cls.RESPONSE_DATA_ID] for camp in response_data[cls.RESPONSE_DATA_KEY]["success"]
        ]
        objects_error: list[str] = [
            sub_error
            for sub_errors in response_data[cls.RESPONSE_DATA_KEY]["error"]
            for sub_error in sub_errors["errors"]
        ]
        return objects_success, objects_error

    def _bulk_create_or_update(self, objects: List[dict], method: str):
        """
        Sends a bulk update or create request to the server for the given list of objects.

        :param objects: A list of dictionaries representing the objects to be updated or created.
        :param method: The HTTP method to be used for the request (e.g. 'POST' or 'PUT').
        :returns: A tuple containing a list of successfully created or updated objects and a list of errors.
        """
        batch_size = 1000
        successfull = []
        errors = []
        for objects_batch in chunker(objects, batch_size):
            response = self.send_request(
                url=self.URL,
                method=method,
                extra_headers=self.HEADERS,
                body={self.RESPONSE_DATA_KEY: objects_batch},
            )
            objects_success, objects_error = self._parse_response(response)
            successfull.extend(objects_success)
            errors.extend(objects_error)

        return successfull, errors

    def validate_all_data_provided(self):
        for field in [
            self.HEADERS,
            self.URL,
            self.ENTITY,
            self.RESPONSE_DATA_KEY,
            self.RESPONSE_DATA_ID,
        ]:
            if field is None:
                raise NotImplementedError(
                    f"Not all fields ware provided in child class. {field} not provided!"
                )
