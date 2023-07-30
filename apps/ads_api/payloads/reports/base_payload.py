from datetime import date


class BasePayloadMixin:
    BASE_COLUMNS = [
        "date",
        "impressions",
        "cost",
        "purchases30d",
        "clicks",
        "sales30d",
        "campaignId",
        "unitsSoldClicks30d",
        "kindleEditionNormalizedPagesRoyalties14d",
    ]

    def __init__(
        self,
        start_date: date,
        end_date: date,
    ):
        self._start_date = start_date
        self._end_date = end_date

    @staticmethod
    def report_date_formatted(report_date: date) -> str:
        return report_date.strftime("%Y-%m-%d")
