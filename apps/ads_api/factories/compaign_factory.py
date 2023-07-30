import logging
from typing import Optional

from apps.ads_api.campaigns.auto_gp_campaign import AutoGPCampaign
from apps.ads_api.campaigns.broad_research_campaign import BroadResearchCampaign
from apps.ads_api.campaigns.broad_research_single_campaign import (
    BroadResearchSingleCampaign,
)
from apps.ads_api.campaigns.discovery_campaign import DiscoveryCampaign
from apps.ads_api.campaigns.exact_scale_campaign import ExactScaleCampaign
from apps.ads_api.campaigns.exact_scale_single_campaign import ExactScaleSingleCampaign
from apps.ads_api.campaigns.gp_campaign import GPCampaign
from apps.ads_api.campaigns.product.product_comp_campaign import ProductCompCampaign
from apps.ads_api.campaigns.product.product_exp_campaign import ProductExpCampaign
from apps.ads_api.campaigns.product.product_own_campaign import ProductOwnCampaign
from apps.ads_api.campaigns.product.product_self_campaign import ProductSelfCampaign
from apps.ads_api.constants import DEFAULT_MAX_BID
from apps.ads_api.exceptions.ads_api.campaigns import InvalidCampaignPurpose
from apps.ads_api.interfaces.entities.campaign.campaign_creatable_interface import (
    CampaignCreatableInterface,
)
from apps.ads_api.models import Book, CampaignPurpose

_logger = logging.getLogger(__name__)


class CampaignFactory:
    def __init__(
        self,
        book: Book,
        keywords: list[str],
        default_bid: Optional[float] = None,
    ):
        self._default_bid = default_bid
        self._keywords = keywords
        self._book = book

    def choose_campaign_type(self, campaign_purpose: CampaignPurpose) -> CampaignCreatableInterface:
        if campaign_purpose == CampaignPurpose.Discovery:
            campaign = DiscoveryCampaign(book=self._book, bid=self._default_bid)
        elif campaign_purpose == CampaignPurpose.Auto_GP:
            campaign = AutoGPCampaign(book=self._book)
        elif campaign_purpose == CampaignPurpose.Exact_Scale_Single:
            campaign = ExactScaleSingleCampaign(
                book=self._book,
                text_keywords=self._keywords,
                default_bid=self._default_bid,
            )
        elif campaign_purpose == CampaignPurpose.Broad_Research_Single:
            campaign = BroadResearchSingleCampaign(
                book=self._book,
                text_keywords=self._keywords,
                default_bid=self._default_bid,
            )
        elif campaign_purpose == CampaignPurpose.Product_Comp:
            campaign = ProductCompCampaign(
                book=self._book,
                text_targets=self._keywords,
                default_bid=self._default_bid,
            )
        elif campaign_purpose == CampaignPurpose.Product_Own:
            campaign = ProductOwnCampaign(
                book=self._book,
                text_targets=self._keywords,
                default_bid=self._default_bid,
            )
        elif campaign_purpose == CampaignPurpose.Product_Self:
            campaign = ProductSelfCampaign(
                book=self._book,
                text_targets=[self._book.asin],
                default_bid=DEFAULT_MAX_BID,
            )
        elif campaign_purpose == CampaignPurpose.GP:
            campaign = GPCampaign(book=self._book, text_keywords=self._keywords)
        elif campaign_purpose == CampaignPurpose.Exact_Scale:
            campaign = ExactScaleCampaign(
                book=self._book,
                text_keywords=self._keywords,
                default_bid=self._default_bid,
            )
        elif campaign_purpose == CampaignPurpose.Broad_Research:
            campaign = BroadResearchCampaign(
                book=self._book,
                text_keywords=self._keywords,
                default_bid=self._default_bid,
            )
        elif campaign_purpose == CampaignPurpose.Product_Exp:
            campaign = ProductExpCampaign(
                book=self._book,
                text_targets=self._keywords,
                default_bid=self._default_bid,
            )
        else:
            _logger.info("Campaign purpose invalid. Exiting...")
            raise InvalidCampaignPurpose()

        return campaign
