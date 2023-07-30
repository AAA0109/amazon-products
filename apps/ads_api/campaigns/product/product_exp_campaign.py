from apps.ads_api.campaigns.product.base_product_campaign import BaseProductCampaign
from apps.ads_api.constants import TargetingExpressionPredicateType
from apps.ads_api.models import CampaignPurpose


class ProductExpCampaign(
    BaseProductCampaign
):
    CAMPAIGN_PURPOSE = CampaignPurpose.Product_Exp
    RESOLVED_EXPRESSION_TYPE = TargetingExpressionPredicateType.ASIN_EXPANDED_FROM
