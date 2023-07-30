# from mock import patch
#
# from apps.ads_api.constants import SpReportType
# from apps.ads_api.entities.amazon_ads.reports import (
#     KeywordQueryReportDataEntity,
#     TargetsReportData,
#     KeywordsReportDataEntity,
#     CampaignsReportDataEntity,
#     PlacementsReportDataEntity,
#     ProductAdsReportData,
#     TargetQueryReportDataEntity,
# )
# from apps.ads_api.services.amazon.reports.download_from_amazon_service import (
#     DownloadReportService,
# )
#
#
# def test_response_has_empty_list():
#     with patch(
#         "apps.ads_api.services.amazon.amazon_request_service.AmazonRequestService.do_request"
#     ):
#         service = DownloadReportService()
#         with patch("apps.utils.gzip.GzipExtracter.extract") as gzip_mock:
#             gzip_mock.return_value = []
#             reports_data = service.download("server", 1, "url", "report_type")
#             assert reports_data == []
#
#
# def test_response_for_keyword_query(keyword_query_response_content):
#     with patch(
#         "apps.ads_api.services.amazon.amazon_request_service.AmazonRequestService.do_request"
#     ):
#         service = DownloadReportService()
#         with patch("apps.utils.gzip.GzipExtracter.extract") as gzip_mock:
#             gzip_mock.return_value = [keyword_query_response_content]
#             reports_data = service.download(
#                 "server", 1, "url", SpReportType.KEYWORD_QUERY
#             )
#             _assert_report_data_entity_with_response(
#                 keyword_query_response_content, reports_data, SpReportType.KEYWORD_QUERY
#             )
#
#
# def test_response_for_campaigns(campaigns_response_content):
#     with patch(
#         "apps.ads_api.services.amazon.amazon_request_service.AmazonRequestService.do_request"
#     ):
#         service = DownloadReportService()
#         with patch("apps.utils.gzip.GzipExtracter.extract") as gzip_mock:
#             gzip_mock.return_value = [campaigns_response_content]
#             reports_data = service.download("server", 1, "url", SpReportType.CAMPAIGN)
#             _assert_report_data_entity_with_response(
#                 campaigns_response_content, reports_data, SpReportType.CAMPAIGN
#             )
#
#
# def test_response_for_keywords(keywords_response_content):
#     with patch(
#         "apps.ads_api.services.amazon.amazon_request_service.AmazonRequestService.do_request"
#     ):
#         service = DownloadReportService()
#         with patch("apps.utils.gzip.GzipExtracter.extract") as gzip_mock:
#             gzip_mock.return_value = [keywords_response_content]
#             reports_data = service.download("server", 1, "url", SpReportType.KEYWORD)
#             _assert_report_data_entity_with_response(
#                 keywords_response_content, reports_data, SpReportType.KEYWORD
#             )
#
#
# def test_response_for_placements(placements_response_content):
#     with patch(
#         "apps.ads_api.services.amazon.amazon_request_service.AmazonRequestService.do_request"
#     ):
#         service = DownloadReportService()
#         with patch("apps.utils.gzip.GzipExtracter.extract") as gzip_mock:
#             gzip_mock.return_value = [placements_response_content]
#             reports_data = service.download("server", 1, "url", SpReportType.PLACEMENT)
#             _assert_report_data_entity_with_response(
#                 placements_response_content, reports_data, SpReportType.PLACEMENT
#             )
#
#
# def test_response_for_product_ads(product_ads_response_content):
#     with patch(
#         "apps.ads_api.services.amazon.amazon_request_service.AmazonRequestService.do_request"
#     ):
#         service = DownloadReportService()
#         with patch("apps.utils.gzip.GzipExtracter.extract") as gzip_mock:
#             gzip_mock.return_value = [product_ads_response_content]
#             reports_data = service.download("server", 1, "url", SpReportType.PRODUCT_AD)
#             _assert_report_data_entity_with_response(
#                 product_ads_response_content, reports_data, SpReportType.PRODUCT_AD
#             )
#
#
# def test_response_for_target_query(target_query_response_content):
#     with patch(
#         "apps.ads_api.services.amazon.amazon_request_service.AmazonRequestService.do_request"
#     ):
#         service = DownloadReportService()
#         with patch("apps.utils.gzip.GzipExtracter.extract") as gzip_mock:
#             gzip_mock.return_value = [target_query_response_content]
#             reports_data = service.download(
#                 "server", 1, "url", SpReportType.TARGET_QUERY
#             )
#             _assert_report_data_entity_with_response(
#                 target_query_response_content, reports_data, SpReportType.TARGET_QUERY
#             )
#
#
# def test_response_for_target(targets_response_content):
#     with patch(
#         "apps.ads_api.services.amazon.amazon_request_service.AmazonRequestService.do_request"
#     ):
#         service = DownloadReportService()
#         with patch("apps.utils.gzip.GzipExtracter.extract") as gzip_mock:
#             gzip_mock.return_value = [targets_response_content]
#             reports_data = service.download("server", 1, "url", SpReportType.TARGET)
#             _assert_report_data_entity_with_response(
#                 targets_response_content, reports_data, SpReportType.TARGET
#             )
#
#
# def _assert_report_data_entity_with_response(
#     response_content, reports_data, report_type: SpReportType
# ):
#     classes_map = {
#         SpReportType.TARGET: TargetsReportData,
#         SpReportType.KEYWORD: KeywordsReportDataEntity,
#         SpReportType.CAMPAIGN: CampaignsReportDataEntity,
#         SpReportType.PLACEMENT: PlacementsReportDataEntity,
#         SpReportType.PRODUCT_AD: ProductAdsReportData,
#         SpReportType.KEYWORD_QUERY: KeywordQueryReportDataEntity,
#         SpReportType.TARGET_QUERY: TargetQueryReportDataEntity,
#     }
#     ReportDataEntity = classes_map[report_type]
#     expected = ReportDataEntity(**response_content)
#     expected_report_data = [expected]
#     assert reports_data[0] == expected_report_data[0]
