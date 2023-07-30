import dataclasses

import mock
import pytest
from mock.mock import Mock

from apps.ads_api.campaigns.broad_research_campaign import BroadResearchCampaign
from apps.ads_api.constants import MatchType, SpState
from apps.ads_api.models import Book, Keyword


@pytest.mark.django_db
@mock.patch(
    "apps.ads_api.services.campaigns.format_negatives_craetion_service.FormatNegativesCreationService.add_format_negatives_to_campagins"
)
@mock.patch("apps.ads_api.campaigns.base_campaign.BaseCampaign.create_campaign")
@mock.patch("apps.ads_api.campaigns.base_campaign.BaseCampaign.create_ad_group_for_campaign")
@mock.patch("apps.ads_api.campaigns.base_campaign.BaseCampaign.create_product_ad_for_ad_group")
@mock.patch("apps.ads_api.campaigns.broad_research_campaign.BroadResearchCampaign.create_keywords")
@mock.patch("apps.ads_api.adapters.amazon_ads.sponsored_products.targets_adapter.TargetsAdapter.batch_create")
class TestFilterDuplicateKeywordsMixin:
    def test_filter_removes_existing_keywords(
        self,
        create_targets_mock: Mock,
        create_keywords_mock: Mock,
        create_product_ad_mock: Mock,
        create_ad_group_mock: Mock,
        create_campaign_mock: Mock,
        create_format_negatives_mock: Mock,
        campaign,
        profile,
    ):
        book = Book.objects.create(
            asin="test_asin",
            title="test_title",
            profile=profile,
        )

        campaign.profile = profile
        campaign.books.add(book)
        campaign.state = SpState.ENABLED.value
        campaign.save()

        Keyword.objects.create(
            keyword_id=1,
            campaign=campaign,
            keyword_type="Positive",
            match_type=MatchType.BROAD.value,
            keyword_text="test keyword to be deleted",
        )
        create_keywords_mock.return_value = [None, None]
        create_campaign_mock.return_value = Mock(external_id="1")
        create_ad_group_mock.return_value = Mock(external_id="1")

        test_campaign = BroadResearchCampaign(
            book, ["test keyword to be deleted", "test keyword to be created"]
        )
        test_campaign.create()

        assert "test keyword to be deleted" not in create_keywords_mock.mock_calls[0].args[0][0].values()
