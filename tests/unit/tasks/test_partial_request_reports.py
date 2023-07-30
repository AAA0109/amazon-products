import datetime

import mock
import pytest
from django.test import override_settings
from mock import Mock

from apps.ads_api.tasks import partial_request_reports


class TestPartialRequestReports:
    @pytest.mark.django_db
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch(
        "apps.ads_api.services.reports.request_per_dates_service.RequestPerDatesService.request",
        return_value=Mock(),
    )
    def test_request_service_called_3_times(self, service_request_mock: Mock, profile):
        partial_request_reports.delay(profile_ids=[profile.id])

        assert service_request_mock.call_count == 4
