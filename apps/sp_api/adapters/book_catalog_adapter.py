from apps.sp_api.adapters.base_adapter import BaseSpApiAdapter
from apps.sp_api.constants import BaseSpApiUrls, MARKETPLACES


class BookCatalogAdapter(BaseSpApiAdapter):
    def __init__(self, profile):
        super().__init__(profile.profile_server)
        self.country_code = profile.country_code

    def get_book_catalog(self, asin: str):
        # url = f"{BaseSpApiUrls[self.server_location]}/catalog/2022-04-01/items/{asin}?marketplaceIds={MARKETPLACES[self.country_code]}&includedData=attributes,salesRanks"
        params = {
            "marketplaceIds": "ATVPDKIKX0DER",
            "includedData": "attributes,salesRanks"
        }
        headers = {
            "Accept": "application/json "
        }
        url = f"{BaseSpApiUrls[self.server_location]}/catalog/2022-04-01/items/B08D6Z4H36"
        response = self.send_request(url, params=params, extra_headers=headers)
        return response.json()