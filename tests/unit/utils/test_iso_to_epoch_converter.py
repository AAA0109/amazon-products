from datetime import datetime

from apps.ads_api.constants import TimeUnit
from apps.utils.iso_to_epoch_converter import IsoToEpochConverter


class TestIsoToEpochConverter:
    def test_iso_to_epoch_ms_string(self):
        iso_string = "2022-07-12T15:34:21.235Z"
        expected_epoch_ms = 1657640061235
        converter = IsoToEpochConverter()
        assert converter.iso_to_epoch(iso_string, TimeUnit.MILLISECOND) == expected_epoch_ms

    def test_iso_to_epoch_ms_datetime(self):
        date_time = datetime(2022, 7, 12, 15, 34, 21, 235000)
        expected_epoch_ms = 1657640061235
        converter = IsoToEpochConverter()
        assert converter.iso_to_epoch(date_time, TimeUnit.MILLISECOND) == expected_epoch_ms
