import logging

from apps.ads_api.adapters.amazon_ads.sponsored_products.ad_group_adapter import (
    AdGroupAdapter,
)
from apps.ads_api.constants import DEFAULT_BID, QueryTermMatchType
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.search_filters import (
    AdGroupSearchFilter,
    TextFilter,
)
from apps.ads_api.exceptions.ads_api.base import ObjectNotCreatedError
from apps.ads_api.models import AdGroup, Book

_logger = logging.getLogger(__name__)


class SyncCreateAdGroupService:
    def __init__(self, book: Book) -> None:
        self.book = book

    def create_ad_group(self, campaign: CampaignEntity, bid: float = DEFAULT_BID) -> AdGroupEntity:
        """
        Create an ad group for the given campaign in the Amazon Advertising API and the local database.

        Args:
            campaign (CampaignEntity): A `CampaignEntity` instance containing the details of
                the campaign for which to create an ad group.
            bid (float, optional): The default bid for the ad group. Defaults to `DEFAULT_BID`.

        Returns:
            AdGroupEntity: A `AdGroupEntity` instance representing the created ad group.

        Raises:
            ObjectNotCreatedError: If the ad group could not be created in the Amazon Advertising API
                due to an error.

        """
        _logger.info("Creating ad group for campaign %s", campaign.external_id)
        ad_group_adapter = AdGroupAdapter(self.book.profile)
        ad_group = AdGroupEntity(campaign_id=campaign.external_id, name=campaign.name, bid=bid)
        try:
            ad_group.external_id = ad_group_adapter.create(ad_group.dict(by_alias=True, exclude_none=True))
            _logger.info("Ad group sucessfully created, external_id=%s.", ad_group.external_id)
        except ObjectNotCreatedError as e:
            if "duplicateValueError" not in e.errors[0].values():
                raise ObjectNotCreatedError(e.errors) from e

            _logger.warning("External errors: %s.", e.errors[0].values())
            _logger.info("Retrieving ad group with name: %s.", ad_group.name)
            ad_group_filter = AdGroupSearchFilter(
                name_filter=TextFilter(
                    query_term_match_type=QueryTermMatchType.EXACT_MATCH,
                    include=[ad_group.name],
                )
            )
            ad_groups = ad_group_adapter.list(ad_group_filter)
            _logger.info("Ad groups found: %s.", ad_groups)

            if len(ad_groups) > 0:
                ad_group.external_id = ad_groups[0].external_id
                _logger.info("Ad group with external id %s found.", ad_group.external_id)
                ad_group_db, created = AdGroup.objects.update_or_create(
                    campaign_id=campaign.internal_id,
                    ad_group_id=ad_group.external_id,
                    defaults=dict(
                        ad_group_name=ad_group.name,
                    ),
                )
                ad_group.internal_id = ad_group_db.id
                _logger.info(
                    "Ad group created=%s, external_id=%s, internal_id=%s, name=%s.",
                    created,
                    ad_group.external_id,
                    ad_group.internal_id,
                    ad_group.name,
                )
            else:
                raise ObjectNotCreatedError(e.errors)
        else:
            ad_group_db = AdGroup.objects.create(
                campaign_id=campaign.internal_id,
                ad_group_id=ad_group.external_id,
                ad_group_name=ad_group.name,
            )

            ad_group.internal_id = ad_group_db.id
            _logger.info(
                "Ad group witn name %s created, external_id=%s, internal_id=%s.",
                ad_group.name,
                ad_group.external_id,
                ad_group.internal_id,
            )
        return ad_group
