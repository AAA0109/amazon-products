from time import sleep
from typing import Union

from sp_api.api import CatalogItems
from sp_api.base import Marketplaces

from apps.ads_api.constants import ServerLocation
from apps.sp_api.credentials import credentials


class BookSearch:
    def __init__(self, server_location: Union[ServerLocation, str]):
        self.server_location = server_location

    def search_books(
        self,
        keywords: list[str],
        classification_id: int,
        marketplace: Marketplaces,
        max_results: int = 300,
        requests_delay: int = 1,
    ):
        asins_collected = []

        catalog_items = CatalogItems(credentials=credentials[self.server_location], marketplace=marketplace)

        for keywords_to_search in keywords:
            next_token = True
            formatted_keywords = keywords_to_search.lower().split()
            while next_token and len(asins_collected) < max_results:
                response = catalog_items.search_catalog_items(
                    keywords=formatted_keywords,
                    marketplaceIds=[marketplace.marketplace_id],
                    classificationIds=[classification_id],
                    includedData=["summaries", "salesRanks"],
                    pageSize=20,
                    pageToken=next_token if isinstance(next_token, str) else "",
                )
                sleep(requests_delay)

                new_asins = [item["asin"] for item in response.payload["items"]]
                asins_collected.extend(new_asins)

                # Check if we have reached the max_results, if yes then break from the loop
                if len(asins_collected) >= max_results:
                    asins_collected = asins_collected[:max_results]
                    break

                next_token = response.pagination.get("nextToken")

            # If we have reached the max_results, break the loop of keywords as well
            if len(asins_collected) >= max_results:
                break

        return asins_collected
