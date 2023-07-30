import logging

from apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter import BaseSponsoredProductsAdapter
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity

_logger = logging.getLogger(__name__)


class CampaignAdapter(BaseSponsoredProductsAdapter):
    HEADERS = {
        "Accept": "application/vnd.spcampaign.v3+json",
        "Content-Type": "application/vnd.spcampaign.v3+json",
    }
    URL = "/sp/campaigns"
    ENTITY = CampaignEntity
    RESPONSE_DATA_KEY = "campaigns"
    RESPONSE_DATA_ID = "campaignId"
