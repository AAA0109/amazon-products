from apps.ads_api.constants import CampaignTargetingType
from apps.ads_api.models import CampaignPurpose


class TargetingTypeService:
    def __init__(self, campaign_purpose: CampaignPurpose):
        self.campaign_purpose = campaign_purpose

    def get_targeting_type(self) -> CampaignTargetingType:
        targeting_type = CampaignTargetingType.AUTO
        if (
            CampaignPurpose.Discovery not in self.campaign_purpose
            and CampaignPurpose.Auto_GP not in self.campaign_purpose
        ):
            targeting_type = CampaignTargetingType.MANUAL

        return targeting_type
