import pytest

from apps.ads_api.entities.amazon_ads.sponsored_products.targets import TargetEntity
from apps.ads_api.models import Campaign
from apps.ads_api.repositories.targets.recreate_targets_repository import (
    RecreateTargetsRepository,
)
from tests.unit.repositories.targets.test_recrate_targets_repository import _logger


@pytest.mark.django_db
class TestRecreateKeywordsRepository:
    def test_recreate_targets_repository(
        self, campaign, targets_to_recreate, expected_target_enity: TargetEntity
    ):
        campaign = Campaign.objects.filter(id=campaign.id).values(
            "campaign_id_amazon",
            "campaign_name",
            "id",
            "ad_groups__default_bid",
            "ad_groups__ad_group_id",
            "product_ads__product_ad_id",
            "books",
        )[0]

        targets = RecreateTargetsRepository.retrieve_targets_to_recraete(campaign)

        _logger.debug(targets)
        assert targets == [expected_target_enity.dict(exclude_none=True, by_alias=True)]
