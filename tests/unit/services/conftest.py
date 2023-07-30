import pytest

from apps.ads_api.constants import ReportStatus
from apps.ads_api.entities.amazon_ads.reports import ReportEntity


@pytest.fixture
def completed_report_from_response():
    return ReportEntity(
        report_id="123223id",
        report_location="test/report/location",
        report_size=34,
        report_status=ReportStatus.COMPLETED,
        report_type="targets",
    )


@pytest.fixture(scope="module")
def keyword_query_response_content():
    return {
        "keywordId": 1,
        "attributedSales30d": 0,
        "cost": 0.02,
        "attributedUnitsOrdered30d": 0,
        "attributedKindleEditionNormalizedPagesRoyalties14d": 0,
        "adGroupName": "palabras clave",
        "campaignId": 1,
        "matchType": "EXACT",
        "query": "wycoff",
        "impressions": 2,
        "adGroupId": 1,
        "keywordText": "wycoff",
        "clicks": 1,
    }


@pytest.fixture(scope="module")
def campaigns_response_content():
    return {
        "attributedSales30d": 0,
        "cost": 0.1,
        "attributedUnitsOrdered30d": 0,
        "attributedKindleEditionNormalizedPagesRoyalties14d": 0,
        "campaignId": 1,
        "clicks": 0,
        "impressions": 3,
    }


@pytest.fixture(scope="module")
def keywords_response_content():
    return {
        "keywordId": 1,
        "attributedSales30d": 0,
        "cost": 0.1,
        "attributedUnitsOrdered30d": 0,
        "attributedKindleEditionNormalizedPagesRoyalties14d": 0,
        "adGroupName": "GID",
        "campaignId": 1,
        "matchType": "BROAD",
        "clicks": 0,
        "impressions": 0,
        "adGroupId": 1,
        "keywordText": "get it done calendar",
    }


@pytest.fixture(scope="module")
def placements_response_content():
    return {
        "attributedSales30d": 0,
        "cost": 0.3,
        "attributedUnitsOrdered30d": 0,
        "attributedKindleEditionNormalizedPagesRoyalties14d": 0,
        "campaignId": 1,
        "clicks": 0,
        "placement": "Detail Page on-Amazon",
        "impressions": 3,
    }


@pytest.fixture(scope="module")
def product_ads_response_content():
    return {
        "attributedSales30d": 0,
        "adId": 1,
        "cost": 1.0,
        "attributedUnitsOrdered30d": 0,
        "attributedKindleEditionNormalizedPagesRoyalties14d": 0,
        "adGroupName": "TAPSS-SP-Phrase-GP-B09YQLT5L7-Paperback",
        "campaignId": 1,
        "clicks": 0,
        "asin": "B09YQLT5L7",
        "impressions": 158,
        "adGroupId": 1,
    }


@pytest.fixture(scope="module")
def target_query_response_content():
    return {
        "attributedSales30d": 0,
        "cost": 1.07,
        "targetId": 1,
        "attributedUnitsOrdered30d": 0,
        "attributedKindleEditionNormalizedPagesRoyalties14d": 0,
        "adGroupName": "INCC-SP-Product-Comp-5-B08WZCVC1D-Paperback",
        "campaignId": 1,
        "query": "b08zvzkd2h",
        "impressions": 5,
        "targetingExpression": 'asin="B08ZVZKD2H"',
        "adGroupId": 1,
        "targetingText": 'asin="B08ZVZKD2H"',
        "clicks": 1,
        "targetingType": "TARGETING_EXPRESSION",
    }


@pytest.fixture(scope="module")
def targets_response_content():
    return {
        "attributedSales30d": 0,
        "cost": 0.01,
        "targetId": 1,
        "attributedUnitsOrdered30d": 0,
        "attributedKindleEditionNormalizedPagesRoyalties14d": 0,
        "adGroupName": "Common Cents CA-Auto Test",
        "campaignId": 1,
        "impressions": 0,
        "targetingExpression": "close-match",
        "adGroupId": 1,
        "targetingText": "close-match",
        "clicks": 0,
        "targetingType": "TARGETING_EXPRESSION_PREDEFINED",
    }
