import logging

from apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter import (
    CampaignAdapter,
)
from apps.ads_api.constants import QueryTermMatchType
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.search_filters import (
    CampaignSearchFilter,
    TextFilter,
)
from apps.ads_api.exceptions.ads_api.base import ObjectNotCreatedError
from apps.ads_api.models import Book, Campaign
from apps.ads_api.repositories.campaign_repository import CampaignRepository

_logger = logging.getLogger(__name__)


class SyncCreateCampaignService:
    def __init__(self, book: Book) -> None:
        self.book = book

    def create_campaign(self, campaign: CampaignEntity) -> CampaignEntity:
        """
        Creates a new campaign in the Amazon Advertising API and the local database.

        Args:
            campaign (CampaignEntity): A `CampaignEntity` instance containing the details of
                the campaign to be created.

        Returns:
            CampaignEntity: A `CampaignEntity` instance representing the created campaign.

        Raises:
            ObjectNotCreatedError: If the campaign could not be created in the Amazon Advertising API.
        """
        campaign_adapter = CampaignAdapter(self.book.profile)
        _logger.info("Creating campaign for book %s[%s]", self.book, self.book.profile)
        try:
            campaign.external_id = campaign_adapter.create(campaign.dict(by_alias=True, exclude_none=True))
            _logger.info(
                "Campaign with fields %s sucessfuly created on amazon side, external_id %s.",
                campaign.dict(by_alias=True, exclude_none=True),
                campaign.external_id,
            )
        except ObjectNotCreatedError as e:
            if "duplicateValueError" not in e.errors[0].values():
                raise ObjectNotCreatedError(e.errors) from e

            _logger.warning("External errors: %s", e.errors[0].values())
            _logger.info("Campaign[%s] already exists on amazon side.", campaign.name)
            campaign = self._handle_duplicate_exception(campaign)
        else:
            campaign_db = Campaign.objects.create(
                campaign_id_amazon=campaign.external_id,
                profile=self.book.profile,
                targeting_type=campaign.targeting_type,
                campaign_name=campaign.name,
                managed=True,
                asins=[self.book.asin],
                campaign_purpose=campaign.campaign_purpose,
            )
            CampaignRepository.add_books_for_campaign(campaign_db, (self.book,))

            campaign.internal_id = campaign_db.id
            _logger.info(
                "Campaign with name %s created locally, local id: %s, external id: %s.",
                campaign_db.campaign_name,
                campaign_db.id,
                campaign_db.campaign_id_amazon,
            )
        _logger.info("Campaign created internally and externally, campaign details: %s.", campaign.dict())
        return campaign

    def _handle_duplicate_exception(self, campaign: CampaignEntity):
        _logger.info("Trying to retrieve campaign with name %s from amazon.", campaign.name)
        campaign_filter = CampaignSearchFilter(
            name_filter=TextFilter(
                query_term_match_type=QueryTermMatchType.EXACT_MATCH,
                include=[campaign.name],
            )
        )
        campaign_adapter = CampaignAdapter(self.book.profile)
        campaigns = campaign_adapter.list(campaign_filter)
        _logger.info("All campaigns found: %s", campaigns)
        if len(campaigns) > 0:
            campaign.external_id = campaigns[0].external_id
            _logger.info("Campaign with name %s found external_id %s.", campaign.name, campaign.external_id)
            campaign_db, created = Campaign.objects.update_or_create(
                campaign_id_amazon=campaign.external_id,
                defaults=dict(
                    profile=self.book.profile,
                    targeting_type=campaign.targeting_type,
                    campaign_name=campaign.name,
                    managed=True,
                    asins=[self.book.asin],
                    campaign_purpose=campaign.campaign_purpose,
                ),
            )
            CampaignRepository.add_books_for_campaign(campaign_db, (self.book,))
            campaign.internal_id = campaign_db.id
            _logger.info(
                "Campaign created=%s name=%s, external_id=%s, internal_id=%s.",
                created,
                campaign.name,
                campaign.external_id,
                campaign.internal_id,
            )
        return campaign
