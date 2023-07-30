# import pytest
# from mock.mock import patch, Mock
#
# from apps.ads_api.constants import ReportStatus
# from apps.ads_api.entities.amazon_ads.reports import (
#     BaseReportDataEntity, ReportEntity,
# )
# from apps.ads_api.exceptions.ads_api.reports import NoReportDataReturned
# from apps.ads_api.models import Report
# from apps.ads_api.services.reports.download_reports_service import \
#     DownloadReportsService
#
#
# @pytest.mark.django_db
# @patch("apps.ads_api.repositories.report_data_repository.ReportDataRepository.create_or_update")
# @patch("apps.ads_api.services.reports.download_reports_service.DownloadReportsService._is_report_data_should_be_saved")
# @patch("apps.ads_api.services.amazon.reports.download_from_amazon_service.DownloadReportService.download")
# class TestDownloadReportsService:
#     def test_download(
#         self,
#         mock_download,
#         mock_is_report_data_should_be_saved,
#         mock_create_or_update
#     ):
#         report = Report.objects.create(
#             report_id=f"report_id_1",
#             report_status=ReportStatus.COMPLETED,
#         )
#         report_entity = ReportEntity(
#             report_id=report.report_id,
#             report_status=report.report_status,
#             report_type=report.report_type,
#             report_size=report.report_size,
#             report_for_date=report.report_for_date,
#             report_server=report.report_server,
#             profile_id=report.profile_id,
#             report_location=report.report_location,
#         )
#         mock_downloaded_report = Mock(spec=BaseReportDataEntity)
#         mock_download.return_value = [mock_downloaded_report]
#         mock_is_report_data_should_be_saved.return_value = True
#
#         service = DownloadReportsService()
#         service.download()
#
#         mock_download.assert_called_once_with(report_entity)
#         mock_is_report_data_should_be_saved.assert_called_once_with(
#             mock_downloaded_report
#         )
#         mock_create_or_update.assert_called_once_with(
#             mock_downloaded_report
#         )
#         report.refresh_from_db()
#         assert report.report_status == ReportStatus.INTERNAL_PROCESSED.value
#
#     def test_download_no_report_data_returned(
#         self,
#         mock_download,
#         mock_is_report_data_should_be_saved,
#         mock_create_or_update_from_report_data
#     ):
#         report = Report.objects.create(
#             report_id=f"report_id_1",
#             report_status=ReportStatus.COMPLETED,
#         )
#         report_entity = ReportEntity(
#             report_id=report.report_id,
#             report_status=report.report_status,
#             report_type=report.report_type,
#             report_size=report.report_size,
#             report_for_date=report.report_for_date,
#             report_server=report.report_server,
#             profile_id=report.profile_id,
#             report_location=report.report_location,
#         )
#         mock_download.return_value = []
#         mock_download.side_effect = NoReportDataReturned()
#
#         service = DownloadReportsService()
#         service.download()
#
#         mock_download.assert_called_once_with(report_entity)
#         mock_is_report_data_should_be_saved.assert_not_called()
#         mock_create_or_update_from_report_data.assert_not_called()
#         report.refresh_from_db()
#         assert report.report_status == ReportStatus.INTERNAL_FAILURE.value
#
#     @patch("apps.ads_api.services.reports.download_reports_service.DownloadReportsService._save_to_non_existent_campaigns")
#     def test_download_report_data_should_not_be_saved(
#         self,
#         mock_save_to_non_existent_campaigns,
#         mock_download,
#         mock_is_report_data_should_be_saved,
#         mock_create_or_update_from_report_data,
#     ):
#         report = Report.objects.create(
#             report_id=f"report_id_1",
#             report_status=ReportStatus.COMPLETED,
#         )
#         report_entity = ReportEntity(
#             report_id=report.report_id,
#             report_status=report.report_status,
#             report_type=report.report_type,
#             report_size=report.report_size,
#             report_for_date=report.report_for_date,
#             report_server=report.report_server,
#             profile_id=report.profile_id,
#             report_location=report.report_location,
#         )
#         mock_downloaded_report = Mock(spec=BaseReportDataEntity)
#         mock_download.return_value = [mock_downloaded_report]
#         mock_is_report_data_should_be_saved.return_value = False
#
#         service = DownloadReportsService()
#         service.download()
#
#         mock_download.assert_called_once_with(report_entity)
#         mock_is_report_data_should_be_saved.assert_called_once_with(
#             mock_downloaded_report
#         )
#         mock_create_or_update_from_report_data.assert_not_called()
#         mock_save_to_non_existent_campaigns.assert_called_once_with(
#             profile_id=report.profile_id, report_data=mock_downloaded_report
#         )
#         report.refresh_from_db()
#         assert report.report_status == ReportStatus.COMPLETED.value
