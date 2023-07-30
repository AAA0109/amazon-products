from apps.ads_api.constants import CampaignType
from apps.ads_api.models import Book, Campaign, CampaignPurpose
from apps.utils.acronyms import generate_acronym


class CampaignNameGeneratorService:
    def __init__(
        self,
        campaign_purpose: CampaignPurpose,
        book: Book,
        created_campaigns_count: int = 0,
    ):
        self.book = book
        self.campaign_purpose = campaign_purpose
        self.name = None
        self.created_campaigns = created_campaigns_count

    def get_name(self):
        """
        Result e.g.: ABCDE-SP-Broad-Research-5-000ASIN000-Paperback
        """
        if self.name is None:
            name = "-".join(
                (
                    generate_acronym(self.book.title),
                    "SP",
                    self.campaign_purpose,
                    self._calculate_campaign_number(),
                    self.book.asin,
                    self.book.format.split(sep=" ")[0],
                )
            )
            self.name = name

        return self.name

    def _calculate_campaign_number(self) -> str:
        existing_campagins_count = Campaign.objects.filter(
            books__asin__contains=self.book.asin,
            profile=self.book.profile,
            books__format=self.book.format,
            campaign_name__contains=self.campaign_purpose,
            sponsoring_type=CampaignType.SPONSORED_PRODUCTS,
        ).count()
        campaign_number = existing_campagins_count + 1
        return str(campaign_number)
