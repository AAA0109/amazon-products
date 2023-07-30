from datetime import datetime
from typing import Union

from apps.ads_api.constants import TimeUnit


class IsoToEpochConverter:
    @staticmethod
    def iso_to_epoch(iso: Union[str, datetime], convert_to: TimeUnit) -> int:
        time_units = {
            TimeUnit.MILLISECOND: 1000,
            TimeUnit.SECOND: 1,
        }
        if type(iso) == str:
            iso = iso.replace("Z", "+00:00")
            iso = datetime.fromisoformat(iso)
        epoch = int(iso.timestamp() * time_units[convert_to])
        return epoch
