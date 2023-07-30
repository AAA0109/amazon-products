from typing import Optional

from apps.ads_api.constants import BiddingStrategies, DEFAULT_DAILY_BUDGET, SpState
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity, Budget
from apps.ads_api.models import CampaignPurpose, Book
from apps.ads_api.services.campaigns.bidding_strategy_service import BiddingStrategyService
from apps.ads_api.services.campaigns.name_generator_service import CampaignNameGeneratorService
from apps.ads_api.services.campaigns.targeting_type_service import TargetingTypeService
from apps.utils.calendar_utils import Calendar


class BuildCampaignEntityService:
    def __init__(self,
                 campaign_purpose: CampaignPurpose,
                 book: Book,
                 bidding_strategy: BiddingStrategies,
                 tos: Optional[int] = None,
                 pp: Optional[int] = None,
                 created_campaigns: list[CampaignEntity] = None
                 ):
        self.created_campaigns = created_campaigns if created_campaigns else []
        self.pp = pp
        self.tos = tos
        self.bidding_strategy = bidding_strategy
        self.book = book
        self.campaign_purpose = campaign_purpose

    def build(self) -> CampaignEntity:
        name_generator = CampaignNameGeneratorService(
            book=self.book,
            campaign_purpose=self.campaign_purpose,
        )
        bidding_strategy = BiddingStrategyService(
            bidding_strategy=self.bidding_strategy,
            tos=self.tos,
            pp=self.pp,
        )
        targeting_type = TargetingTypeService(
            campaign_purpose=self.campaign_purpose,
        )

        campaign = CampaignEntity(
            name=name_generator.get_name(),
            targeting_type=targeting_type.get_targeting_type(),
            start_date=Calendar.today_date_string_for_region(
                self.book.profile.country_code, "%Y-%m-%d"
            ),
            dynamic_bidding=bidding_strategy.get_bidding_strategy(),
            campaign_purpose=self.campaign_purpose,
            state=SpState.ENABLED,
            budget=Budget(budget=DEFAULT_DAILY_BUDGET, budget_type="DAILY")
        )
        return campaign
