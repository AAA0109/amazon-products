import datetime

import pytest
from mock.mock import Mock

from apps.ads_api.adapters.amazon_ads.sponsored_products.product_ad_adapter import ProductAdAdapter
from apps.ads_api.constants import SpState
from apps.ads_api.entities.amazon_ads.sponsored_products.extended_data import ExtendedData
from apps.ads_api.entities.amazon_ads.sponsored_products.product_ad import ProductAdEntity
from apps.ads_api.models import ProductAd
from apps.ads_api.services.product_ads.sync_product_ads_service import SyncProductAdsService


@pytest.fixture
def clean_up_product_ad_after_test():
    yield
    ProductAd.objects.all().delete()


@pytest.mark.django_db
class TestSyncProductAdsService:
    sample_product_ad = ProductAdEntity.parse_obj({
        "campaign_id": 1,
        "ad_group_id": 1,
        "external_id": 1,
        "asin": "134567890",
        "state": SpState.ENABLED.value,
        "extended_data": ExtendedData(**{
            "serving_status": "TEST_SERVING_STATUS",
            "last_update_date_time": datetime.datetime(2022, 7, 12, 15, 34, 21, 235000)
        }),
    })

    campaign_external_id = 1
    ad_group_external_id = 1
    product_ad_external_id = 1

    @pytest.mark.usefixtures('clean_up_product_ad_after_test')
    def test_new_product_ad_created(self, monkeypatch, profile, campaign, ad_group):
        campaign.profile = profile
        campaign.campaign_id_amazon = self.campaign_external_id
        campaign.save()

        ad_group.campaign = campaign
        ad_group.ad_group_id = self.ad_group_external_id
        ad_group.save()

        list_response_mock = Mock(return_value=[self.sample_product_ad])
        monkeypatch.setattr(ProductAdAdapter, "list", list_response_mock)

        product_ad_sync = SyncProductAdsService(profile)
        product_ad_sync.sync()
        created_product_ad = ProductAd.objects.first()

        assert ProductAd.objects.count() == 1
        assert created_product_ad.asin == '134567890'
        assert created_product_ad.state == SpState.ENABLED.value
        assert created_product_ad.last_updated_date_on_amazon == 1657640061235
        assert created_product_ad.serving_status == 'TEST_SERVING_STATUS'
        assert created_product_ad.campaign_id == campaign.id  # Foreign key
        assert created_product_ad.ad_group_id == ad_group.id  # Foreign key
        assert created_product_ad.product_ad_id == self.product_ad_external_id

    def test_existed_product_ad_updated(self, monkeypatch, profile, campaign, ad_group, product_ad):
        campaign.profile = profile
        campaign.campaign_id_amazon = self.campaign_external_id
        campaign.save()

        ad_group.campaign = campaign
        ad_group.ad_group_id = self.ad_group_external_id
        ad_group.save()

        product_ad.campaign = campaign
        product_ad.ad_group = ad_group
        product_ad.product_ad_id = self.product_ad_external_id
        product_ad.state = SpState.PAUSED.value
        product_ad.save()

        list_response_mock = Mock(return_value=[self.sample_product_ad])
        monkeypatch.setattr(ProductAdAdapter, "list", list_response_mock)

        product_ad_sync = SyncProductAdsService(profile)
        product_ad_sync.sync()
        created_product_ad = ProductAd.objects.get(id=product_ad.id)

        assert ProductAd.objects.count() == 1
        assert created_product_ad.asin == '134567890'
        assert created_product_ad.state == SpState.ENABLED.value
        assert created_product_ad.last_updated_date_on_amazon == 1657640061235
        assert created_product_ad.serving_status == 'TEST_SERVING_STATUS'
        assert created_product_ad.campaign_id == campaign.id  # Foreign key
        assert created_product_ad.ad_group_id == ad_group.id  # Foreign key
        assert created_product_ad.product_ad_id == self.product_ad_external_id  # external id

    def test_product_ad_creation_skipped_if_product_ad_exists_and_both_ad_group_and_campaign_not(self, monkeypatch, profile):
        list_response_mock = Mock(return_value=[self.sample_product_ad])
        monkeypatch.setattr(ProductAdAdapter, "list", list_response_mock)

        product_ad_sync = SyncProductAdsService(profile)
        product_ad_sync.sync()

        assert ProductAd.objects.count() == 0
