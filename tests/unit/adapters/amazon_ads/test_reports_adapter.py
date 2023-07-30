import datetime

import mock
import pytest
from mock.mock import Mock

from apps.ads_api.adapters.amazon_ads.reports_adapter import ReportsAdapter
from apps.ads_api.constants import SpReportType, AdProductTypes, TypeIdOfReport, AdStatus, TimeUnitOfReport, \
    FormatOfReport, ServerLocation
from apps.ads_api.exceptions.ads_api.reports import CreatingReportRequestException
from apps.ads_api.models import Report


@pytest.fixture(scope="class")
def sample_report_request() -> dict:
    return {
        "reportId": "8adca409-98e1-442c-9e74-28147f9f7bc8",
        "endDate": "2023-05-30",
        "name": "SponsoredProductsPurchasedProductDailyReport",
        "startDate": "2023-05-15",
        "status": "PENDING",
        "updatedAt": "2022-04-27T13:13:44.054Z"
    }


@pytest.fixture(scope="class")
def reports_adapter():
    def _get_reports_adapter(report_type: SpReportType):
        reports_adapter = ReportsAdapter(
            end_date=datetime.datetime(2023, 5, 30),
            start_date=datetime.datetime(2023, 5, 15),
            report_type=report_type,
            server=ServerLocation.EUROPE
        )
        return reports_adapter

    return _get_reports_adapter


@pytest.fixture(scope="class")
def expected_campaign_payload() -> dict:
    return {
        'startDate': '2023-05-15',
        'endDate': '2023-05-30',
        'configuration': {
            'adProduct': AdProductTypes.SP_PRODUCTS,
            'groupBy': ['campaign'],
            'columns': ['date', 'impressions', 'cost', 'purchases30d', 'clicks', 'sales30d', 'campaignId',
                        'unitsSoldClicks30d', 'kindleEditionNormalizedPagesRoyalties14d', 'topOfSearchImpressionShare'],
            'reportTypeId': TypeIdOfReport.SP_CAMPAIGNS,
            'filters': [
                {'field': 'campaignStatus', 'values': [AdStatus.ENABLED, AdStatus.PAUSED, AdStatus.ARCHIVED]}
            ],
            'timeUnit': TimeUnitOfReport.DAILY, 'format': FormatOfReport.GZIP_JSON
        }
    }


@pytest.fixture(scope="class")
def expected_keywords_payload():
    return {
        'configuration': {'adProduct': AdProductTypes.SP_PRODUCTS,
                          'columns': ['date',
                                      'impressions',
                                      'cost',
                                      'purchases30d',
                                      'clicks',
                                      'sales30d',
                                      'campaignId',
                                      'unitsSoldClicks30d',
                                      'kindleEditionNormalizedPagesRoyalties14d',
                                      'adGroupName',
                                      'adGroupId',
                                      'keywordId',
                                      'keyword',
                                      'matchType'],
                          'filters': [{'field': 'keywordType',
                                       'values': ['BROAD', 'PHRASE', 'EXACT']},
                                      {'field': 'adKeywordStatus',
                                       'values': [AdStatus.ENABLED,
                                                  AdStatus.PAUSED,
                                                  AdStatus.ARCHIVED]}],
                          'format': FormatOfReport.GZIP_JSON,
                          'groupBy': ['targeting'],
                          'reportTypeId': TypeIdOfReport.SP_TARGETING,
                          'timeUnit': TimeUnitOfReport.DAILY},
        'endDate': '2023-05-30',
        'startDate': '2023-05-15'}


@pytest.fixture(scope="class")
def expected_keyword_search_term_payload():
    return {'configuration': {'adProduct': AdProductTypes.SP_PRODUCTS,
                              'columns': ['date',
                                          'impressions',
                                          'cost',
                                          'purchases30d',
                                          'clicks',
                                          'sales30d',
                                          'campaignId',
                                          'unitsSoldClicks30d',
                                          'kindleEditionNormalizedPagesRoyalties14d',
                                          'adGroupName',
                                          'adGroupId',
                                          'keywordId',
                                          'keyword',
                                          'matchType',
                                          'searchTerm'],
                              'filters': [{'field': 'keywordType',
                                           'values': ['BROAD', 'PHRASE', 'EXACT']}],
                              'format': FormatOfReport.GZIP_JSON,
                              'groupBy': ['searchTerm'],
                              'reportTypeId': TypeIdOfReport.SP_SEARCH_TERM,
                              'timeUnit': TimeUnitOfReport.DAILY},
            'endDate': '2023-05-30',
            'startDate': '2023-05-15'}


@pytest.fixture(scope="class")
def expected_placemant_payload():
    return {'configuration': {'adProduct': AdProductTypes.SP_PRODUCTS,
                              'columns': ['date',
                                          'impressions',
                                          'cost',
                                          'purchases30d',
                                          'clicks',
                                          'sales30d',
                                          'campaignId',
                                          'unitsSoldClicks30d',
                                          'kindleEditionNormalizedPagesRoyalties14d',
                                          'placementClassification'],
                              'format': FormatOfReport.GZIP_JSON,
                              'groupBy': ['campaign', 'campaignPlacement'],
                              'reportTypeId': TypeIdOfReport.SP_CAMPAIGNS,
                              'timeUnit': TimeUnitOfReport.DAILY},
            'endDate': '2023-05-30',
            'startDate': '2023-05-15'}


@pytest.fixture(scope="class")
def expected_product_ad_payload():
    return {'configuration': {'adProduct': AdProductTypes.SP_PRODUCTS,
                              'columns': ['date',
                                          'impressions',
                                          'cost',
                                          'purchases30d',
                                          'clicks',
                                          'sales30d',
                                          'campaignId',
                                          'unitsSoldClicks30d',
                                          'kindleEditionNormalizedPagesRoyalties14d',
                                          'adId',
                                          'adGroupName',
                                          'adGroupId',
                                          'advertisedAsin'],
                              'format': FormatOfReport.GZIP_JSON,
                              'groupBy': ['advertiser'],
                              'reportTypeId': TypeIdOfReport.SP_ADVERTISED_PRODUCT,
                              'timeUnit': TimeUnitOfReport.DAILY},
            'endDate': '2023-05-30',
            'startDate': '2023-05-15'}


@pytest.fixture(scope="class")
def expected_target_payload():
    return {'configuration': {'adProduct': AdProductTypes.SP_PRODUCTS,
                              'columns': ['date',
                                          'impressions',
                                          'cost',
                                          'purchases30d',
                                          'clicks',
                                          'sales30d',
                                          'campaignId',
                                          'unitsSoldClicks30d',
                                          'kindleEditionNormalizedPagesRoyalties14d',
                                          'adGroupName',
                                          'adGroupId',
                                          'keywordId',
                                          'keyword',
                                          'targeting',
                                          'keywordType'],
                              'filters': [{'field': 'keywordType',
                                           'values': ['TARGETING_EXPRESSION',
                                                      'TARGETING_EXPRESSION_PREDEFINED']},
                                          {'field': 'adKeywordStatus',
                                           'values': [AdStatus.ENABLED,
                                                      AdStatus.PAUSED,
                                                      AdStatus.ARCHIVED]}],
                              'format': FormatOfReport.GZIP_JSON,
                              'groupBy': ['targeting'],
                              'reportTypeId': TypeIdOfReport.SP_TARGETING,
                              'timeUnit': TimeUnitOfReport.DAILY},
            'endDate': '2023-05-30',
            'startDate': '2023-05-15'}


@pytest.fixture(scope="class")
def expected_target_search_term_payload():
    return {'configuration': {'adProduct': AdProductTypes.SP_PRODUCTS,
                              'columns': ['date',
                                          'impressions',
                                          'cost',
                                          'purchases30d',
                                          'clicks',
                                          'sales30d',
                                          'campaignId',
                                          'unitsSoldClicks30d',
                                          'kindleEditionNormalizedPagesRoyalties14d',
                                          'adGroupName',
                                          'adGroupId',
                                          'keywordId',
                                          'keyword',
                                          'targeting',
                                          'keywordType'],
                              'filters': [{'field': 'keywordType',
                                           'values': ['TARGETING_EXPRESSION',
                                                      'TARGETING_EXPRESSION_PREDEFINED']},
                                          {'field': 'adKeywordStatus',
                                           'values': [AdStatus.ENABLED,
                                                      AdStatus.PAUSED,
                                                      AdStatus.ARCHIVED]}],
                              'format': FormatOfReport.GZIP_JSON,
                              'groupBy': ['targeting'],
                              'reportTypeId': TypeIdOfReport.SP_TARGETING,
                              'timeUnit': TimeUnitOfReport.DAILY},
            'endDate': '2023-05-30',
            'startDate': '2023-05-15'}


class TestReportsAdapter:
    @staticmethod
    def assert_body_called_with(send_request_mock, expected_body):
        assert send_request_mock.call_args.kwargs["body"] == expected_body

    @mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request")
    def test_campaign_payload_generation(
            self,
            send_request_mock: Mock,
            expected_campaign_payload,
            sample_report_request: dict,
            reports_adapter
    ):
        send_request_mock.return_value = Mock(json=lambda: sample_report_request)
        reports_adapter = reports_adapter(SpReportType.CAMPAIGN)
        test_profile_id = 1

        reports_adapter.create_report_request_for_profile(test_profile_id)
        self.assert_body_called_with(send_request_mock, expected_body=expected_campaign_payload)

    @mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request")
    def test_keyword_payload_generation(
            self,
            send_request_mock: Mock,
            expected_keywords_payload,
            sample_report_request: dict,
            reports_adapter
    ):
        send_request_mock.return_value = Mock(json=lambda: sample_report_request)
        reports_adapter = reports_adapter(SpReportType.KEYWORD)
        test_profile_id = 1

        reports_adapter.create_report_request_for_profile(test_profile_id)
        self.assert_body_called_with(send_request_mock, expected_body=expected_keywords_payload)

    @mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request")
    def test_keyword_search_term_payload_generation(
            self,
            send_request_mock: Mock,
            expected_keyword_search_term_payload,
            sample_report_request: dict,
            reports_adapter
    ):
        send_request_mock.return_value = Mock(json=lambda: sample_report_request)
        reports_adapter = reports_adapter(SpReportType.KEYWORD_QUERY)
        test_profile_id = 1

        reports_adapter.create_report_request_for_profile(test_profile_id)
        self.assert_body_called_with(send_request_mock, expected_body=expected_keyword_search_term_payload)

    @mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request")
    def test_placemant_payload_generation(
            self,
            send_request_mock: Mock,
            expected_placemant_payload,
            sample_report_request: dict,
            reports_adapter
    ):
        send_request_mock.return_value = Mock(json=lambda: sample_report_request)
        reports_adapter = reports_adapter(SpReportType.PLACEMENT)
        test_profile_id = 1

        reports_adapter.create_report_request_for_profile(test_profile_id)
        self.assert_body_called_with(send_request_mock, expected_body=expected_placemant_payload)

    @mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request")
    def test_product_ad_payload_generation(
            self,
            send_request_mock: Mock,
            expected_product_ad_payload,
            sample_report_request: dict,
            reports_adapter
    ):
        send_request_mock.return_value = Mock(json=lambda: sample_report_request)
        reports_adapter = reports_adapter(SpReportType.PRODUCT_AD)
        test_profile_id = 1

        reports_adapter.create_report_request_for_profile(test_profile_id)
        self.assert_body_called_with(send_request_mock, expected_body=expected_product_ad_payload)

    @mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request")
    def test_target_payload_generation(
            self,
            send_request_mock: Mock,
            expected_target_payload,
            sample_report_request: dict,
            reports_adapter
    ):
        send_request_mock.return_value = Mock(json=lambda: sample_report_request)
        reports_adapter = reports_adapter(SpReportType.TARGET)
        test_profile_id = 1

        reports_adapter.create_report_request_for_profile(test_profile_id)
        self.assert_body_called_with(send_request_mock, expected_body=expected_target_payload)

    @mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request")
    def test_target_search_term_payload_generation(
            self,
            send_request_mock: Mock,
            expected_target_search_term_payload,
            sample_report_request: dict,
            reports_adapter
    ):
        send_request_mock.return_value = Mock(json=lambda: sample_report_request)
        reports_adapter = reports_adapter(SpReportType.TARGET)
        test_profile_id = 1

        reports_adapter.create_report_request_for_profile(test_profile_id)
        self.assert_body_called_with(send_request_mock, expected_body=expected_target_search_term_payload)

    @mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request")
    def test_report_saved(
            self,
            send_request_mock: Mock,
            expected_target_search_term_payload,
            sample_report_request: dict,
            reports_adapter
    ):
        send_request_mock.return_value = Mock(json=lambda: sample_report_request)
        reports_adapter = reports_adapter(SpReportType.TARGET)
        test_profile_id = 1

        created_report = reports_adapter.create_report_request_for_profile(test_profile_id)

        assert created_report.report_id == "8adca409-98e1-442c-9e74-28147f9f7bc8"
        assert created_report.report_status == "PENDING"
        assert created_report.start_date == datetime.date(2023, 5, 15)
        assert created_report.end_date == datetime.date(2023, 5, 30)
        assert created_report.report_server == ServerLocation.EUROPE.value
        assert created_report.report_type == SpReportType.TARGET.value

    @mock.patch("apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter.BaseAmazonAdsAdapter.send_request")
    def test_report(
            self,
            send_request_mock: Mock,
            expected_target_search_term_payload,
            sample_report_request: dict,
            reports_adapter
    ):
        send_request_mock.side_effect = Exception
        reports_adapter = reports_adapter(SpReportType.TARGET)
        test_profile_id = 1

        with pytest.raises(CreatingReportRequestException):
            reports_adapter.create_report_request_for_profile(test_profile_id)
