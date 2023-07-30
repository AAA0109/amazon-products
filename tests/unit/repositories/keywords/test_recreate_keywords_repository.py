import logging

import pytest

from apps.ads_api.constants import MatchType
from apps.ads_api.entities.amazon_ads.sponsored_products.keywords import KeywordEntity
from apps.ads_api.models import Campaign, Keyword
from apps.ads_api.repositories.keywords.keywords_repository import KeywordsRepository

_logger = logging.getLogger(__name__)


@pytest.fixture
def keywords_to_recreate(campaign, ad_group):
    ad_group.campaign = campaign
    ad_group.save()

    Keyword.objects.create(
        campaign=campaign,
        ad_group_id=ad_group.ad_group_id,
        keyword_text="test keyword text",
        bid=0.67,
        state="ENABLED",
        match_type=MatchType.EXACT.value,
    )


@pytest.fixture
def expected_keyword_enity() -> KeywordEntity:
    return KeywordEntity.parse_obj(
        {
            "campaignId": "123",
            "adGroupId": "1",
            "keywordText": "test keyword text",
            "matchType": "BROAD",
            "bid": 0.67,
            "state": "ENABLED",
            "matchType": MatchType.EXACT,
        }
    )


class TestRecreateKeywordsRepository:
    @pytest.mark.django_db
    def test_retrieve_keywords_to_recreate(
        self, campaign, keywords_to_recreate, expected_keyword_enity: KeywordEntity
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

        keywords = KeywordsRepository.retrieve_keywords_to_recreate(campaign)

        _logger.debug(keywords)
        assert keywords == [expected_keyword_enity.dict(exclude_none=True, by_alias=True)]
