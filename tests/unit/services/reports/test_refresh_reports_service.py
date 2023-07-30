import pytest
from mock.mock import patch

from apps.ads_api.constants import ReportStatus
from apps.ads_api.exceptions.ads_api.reports import (
    StillGeneratingReportException,
    RefreshingReportException,
)
from apps.ads_api.models import Report
from apps.ads_api.repositories.report_repository import ReportRepository
from apps.ads_api.services.reports.refresh_report_service import RefreshReportService


@pytest.mark.django_db
@patch(
    "apps.ads_api.services.amazon.reports.fetch_from_amazon_service.FetchReportDetailsService.fetch"
)
def test_reports_updates_with_new_data(
    amazon_ads_call_mock,
    completed_report_from_response,
        in_progress_report_entity_from_response,
):
    test_report_id = "test_report_id_1"
    test_location = "test_location"
    test_profile_id = 1
    test_report_size = 32
    completed_report_from_response.report_id = test_report_id
    completed_report_from_response.report_location = test_location
    completed_report_from_response.report_size = test_report_size
    amazon_ads_call_mock.return_value = completed_report_from_response
    in_progress_report_entity_from_response.report_location = test_location
    in_progress_report_entity_from_response.profile_id = test_profile_id
    in_progress_report_entity_from_response.report_id = test_report_id
    ReportRepository.create_from_report(in_progress_report_entity_from_response)

    refresh_report_service = RefreshReportService()
    refresh_report_service.refresh(test_location, test_report_id, test_profile_id)
    report = Report.objects.get(report_id=test_report_id)

    assert report.report_id == completed_report_from_response.report_id
    assert report.report_status == completed_report_from_response.report_status
    assert report.report_size == completed_report_from_response.report_size
    assert report.report_location == completed_report_from_response.report_location


@pytest.mark.django_db
@patch(
    "apps.ads_api.services.amazon.reports.fetch_from_amazon_service.FetchReportDetailsService.fetch"
)
def test_report_with_pending_status_raises_exception(
    amazon_ads_call_mock, in_progress_report_entity_from_response
):
    amazon_ads_call_mock.return_value = in_progress_report_entity_from_response
    refresh_report_service = RefreshReportService()
    test_profile_id = 1
    test_report_id = "test_report_id_1"
    test_location = "test_location"

    with pytest.raises(StillGeneratingReportException):
        refresh_report_service.refresh(test_location, test_report_id, test_profile_id)


@pytest.mark.django_db
@patch(
    "apps.ads_api.services.amazon.reports.fetch_from_amazon_service.FetchReportDetailsService.fetch"
)
def test_empty_response_raises_exception(
    amazon_ads_call_mock, in_progress_report_entity_from_response
):
    amazon_ads_call_mock.return_value = None
    refresh_report_service = RefreshReportService()
    test_profile_id = 1
    test_report_id = "test_report_id_1"
    test_location = "test_location"

    with pytest.raises(RefreshingReportException):
        refresh_report_service.refresh(test_location, test_report_id, test_profile_id)


@pytest.mark.django_db
@patch(
    "apps.ads_api.services.amazon.reports.fetch_from_amazon_service.FetchReportDetailsService.fetch",
    return_value=None,
)
def test_report_with_failure_reason_raises_exception_and_saves_as_failure(
    amazon_ads_call_mock, in_progress_report_entity_from_response
):
    report_id = "test_report_id_1"
    location = "test_location"
    profile_id = 1
    failure_reason = "test_failure_reason"
    in_progress_report_entity_from_response.report_location = location
    in_progress_report_entity_from_response.report_location = report_id
    in_progress_report_entity_from_response.profile_id = profile_id
    ReportRepository.create_from_report(in_progress_report_entity_from_response)

    in_progress_report_entity_from_response.failure_reason = failure_reason
    in_progress_report_entity_from_response.report_status = ReportStatus.FAILURE
    amazon_ads_call_mock.return_value = in_progress_report_entity_from_response
    refresh_report_service = RefreshReportService()

    with pytest.raises(RefreshingReportException):
        refresh_report_service.refresh(location, report_id, profile_id)
        stored_report = Report.objects.get(report_id=report_id)
        assert stored_report.failure_reason == failure_reason
