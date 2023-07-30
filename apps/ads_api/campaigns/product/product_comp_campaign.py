import logging

from apps.ads_api.campaigns.product.base_product_campaign import BaseProductCampaign
from apps.ads_api.constants import (
    TargetingExpressionPredicateType, )
from apps.ads_api.models import CampaignPurpose

_logger = logging.getLogger(__name__)


class ProductCompCampaign(
    BaseProductCampaign
):
    CAMPAIGN_PURPOSE = CampaignPurpose.Product_Comp
    RESOLVED_EXPRESSION_TYPE = TargetingExpressionPredicateType.ASIN_SAME_AS
