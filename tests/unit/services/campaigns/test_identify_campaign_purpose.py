import pytest

from apps.ads_api.models import CampaignPurpose
from apps.ads_api.services.campaigns.identify_campaign_purpose_service import IdentifyCampaignPurpose


class TestIdentifyCampaignPurpose:
    @pytest.mark.parametrize(
        "string_with_campaign, expected_purpose", [
            ("We are running an Auto-Discovery-Loose-Match campaign", CampaignPurpose.Discovery_Loose_Match),
            ("We are running an Auto-Discovery-Close-Match campaign", CampaignPurpose.Discovery_Close_Match),
            ("We are running an Auto-Discovery-Complements campaign", CampaignPurpose.Discovery_Complements),
            ("We are running an Auto-Discovery-Substitutes campaign", CampaignPurpose.Discovery_Substitutes),
            ("We are running a Cat-Research campaign", CampaignPurpose.Cat_Research),
            ("We are running a Broad-Research campaign", CampaignPurpose.Broad_Research),
            ("We are running a Broad-Research-Single campaign", CampaignPurpose.Broad_Research_Single),
            ("We are running an Exact-Scale campaign", CampaignPurpose.Exact_Scale),
            ("We are running an Exact-Scale-Single campaign", CampaignPurpose.Exact_Scale_Single),
            ("We are running a Product-Comp campaign", CampaignPurpose.Product_Comp),
            ("We are running a Product-Own campaign", CampaignPurpose.Product_Own),
            ("We are running a Product-Self campaign", CampaignPurpose.Product_Self),
            ("We are running a GP campaign", CampaignPurpose.GP),
            ("We are running an Auto-GP campaign", CampaignPurpose.Auto_GP),
            ("We are running an campaign", ""),
        ]
    )
    def test_identify_campaign_purpose(self, string_with_campaign, expected_purpose):
        assert IdentifyCampaignPurpose.identify_campaign_purpose(string_with_campaign) == expected_purpose
