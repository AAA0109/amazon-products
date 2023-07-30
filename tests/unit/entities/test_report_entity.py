import logging

import pytest

from apps.ads_api.entities.amazon_ads.reports import ProductAdsReportData

_logger = logging.getLogger(__name__)

report_data_objects = [
    (
        "B0BVD6FZ12",
        {
            "adId": 1,
            "adGroupName": "BPFHACP8X1-SP-GP-1-B0BVD6FZ12-Paperback",
            "adGroupId": 1,
            "unitsSoldClicks30d": 1,
            "sales30d": 1,
            "kindleEditionNormalizedPagesRoyalties14d": 1,
            "campaignId": 1,
            "cost": 1,
            "purchases30d": 1,
            "impressions": 1,
            "clicks": 1,
        },
    ),
    (
        "B0BVD6FZ12",
        {
            "adId": 1,
            "adGroupName": "BPFHACP8X1-SP-GP-1-B0BVD6FZ12-P",
            "adGroupId": 1,
            "unitsSoldClicks30d": 1,
            "sales30d": 1,
            "kindleEditionNormalizedPagesRoyalties14d": 1,
            "campaignId": 1,
            "cost": 1,
            "purchases30d": 1,
            "impressions": 1,
            "clicks": 1,
        },
    ),
]


@pytest.fixture
def report_data_without_valid_group_name():
    return {
        "adId": 1,
        "adGroupName": "ad group 1",
        "adGroupId": 1,
        "unitsSoldClicks30d": 1,
        "sales30d": 1,
        "kindleEditionNormalizedPagesRoyalties14d": 1,
        "campaignId": 1,
        "cost": 1,
        "purchases30d": 1,
        "impressions": 1,
        "clicks": 1,
    }


class TestProductAdsReportDataEntity:
    @pytest.mark.parametrize("expected_asin, report_data", report_data_objects)
    def test_asin_retrieved_from_ad_group_name(self, expected_asin, report_data):
        report_data_entity = ProductAdsReportData.parse_obj(report_data)
        _logger.debug(report_data_entity)
        assert report_data_entity.asin == expected_asin

    @pytest.mark.django_db
    def test_asin_retrieved_from_product_ads(self, product_ad, report_data_without_valid_group_name):
        product_ad.asin = "B0BVD6FZ12"
        product_ad.product_ad_id = 1
        product_ad.save()

        report_data_entity = ProductAdsReportData.parse_obj(report_data_without_valid_group_name)
        _logger.debug(report_data_entity)
        assert report_data_entity.asin == "B0BVD6FZ12"
