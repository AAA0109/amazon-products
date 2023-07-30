import logging

import pytest

from apps.ads_api.constants import (
    SpExpressionType,
    SpState,
    TargetingExpressionPredicateType,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.targets import TargetEntity
from apps.ads_api.models import AdGroup, Campaign, Target
from apps.ads_api.repositories.targets.recreate_targets_repository import (
    RecreateTargetsRepository,
)

_logger = logging.getLogger(__name__)


@pytest.fixture
def targets_to_recreate(campaign, ad_group):
    ad_group.campaign = campaign
    ad_group.save()

    Target.objects.create(
        campaign=campaign,
        ad_group_id=ad_group.ad_group_id,
        bid=0.67,
        state=SpState.ENABLED.value,
        resolved_expression_text="targetingasin",
        resolved_expression_type=TargetingExpressionPredicateType.ASIN_SAME_AS.value,
        targeting_type=SpExpressionType.MANUAL.value,
    )


@pytest.fixture
def expected_target_enity() -> TargetEntity:
    return TargetEntity.parse_obj(
        {
            "campaignId": "123",
            "adGroupId": "1",
            "bid": 0.67,
            "state": SpState.ENABLED,
            "expression": [
                {
                    "type": TargetingExpressionPredicateType.ASIN_SAME_AS,
                    "value": "targetingasin",
                }
            ],
            "expression_type": SpExpressionType.MANUAL,
        }
    )


@pytest.mark.django_db
class TestRecreateTargetsRepository:
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
