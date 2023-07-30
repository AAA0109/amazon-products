from typing import Optional

from apps.ads_api.models import CampaignPurpose


class IdentifyCampaignPurpose:
    @classmethod
    def identify_campaign_purpose(cls, name: str) -> Optional[CampaignPurpose]:
        """
        Identify the campaign purpose from a given campaign name.

        :param name: A string that may contain the name of a campaign purpose.
        :return: The name of the campaign purpose as a CampaignPurpose, or '' if no match is found.
        """
        campaign_purpose = ""
        if "GP" in name and "Auto" not in name:
            campaign_purpose = CampaignPurpose.GP
        elif "Auto-GP" in name:
            campaign_purpose = CampaignPurpose.Auto_GP
        elif "Product-Self" in name:
            campaign_purpose = CampaignPurpose.Product_Self
        elif "Product-Own" in name:
            campaign_purpose = CampaignPurpose.Product_Own
        elif "Product-Comp" in name:
            campaign_purpose = CampaignPurpose.Product_Comp
        elif "Exact-Scale-Single" in name:
            campaign_purpose = CampaignPurpose.Exact_Scale_Single
        elif "Exact-Scale" in name and "Single" not in name:
            campaign_purpose = CampaignPurpose.Exact_Scale
        elif "Broad-Research-Single" in name:
            campaign_purpose = CampaignPurpose.Broad_Research_Single
        elif "Broad-Research" in name and "Single" not in name:
            campaign_purpose = CampaignPurpose.Broad_Research
        elif "Cat-Research" in name:
            campaign_purpose = CampaignPurpose.Cat_Research
        elif "Auto-Discovery-Loose-Match" in name:
            campaign_purpose = CampaignPurpose.Discovery_Loose_Match
        elif "Auto-Discovery-Close-Match" in name:
            campaign_purpose = CampaignPurpose.Discovery_Close_Match
        elif "Auto-Discovery-Substitutes" in name:
            campaign_purpose = CampaignPurpose.Discovery_Substitutes
        elif "Auto-Discovery-Complements" in name:
            campaign_purpose = CampaignPurpose.Discovery_Complements

        return campaign_purpose
