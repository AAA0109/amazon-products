import calendar
import datetime

from apps.ads_api.constants import TIME_LIMITS


class Calendar:
    @staticmethod
    def days_in_month_remaining():
        month_days_count = calendar.monthrange(
            datetime.datetime.today().year, datetime.datetime.today().month
        )[1]
        days_in_month_remaining = month_days_count - datetime.datetime.today().day
        return days_in_month_remaining


    @staticmethod
    def today_date_string_for_region(country_code: str, str_format: str):
        """Returns campaign start date as today, allowing for countries ahead of GMT"""
        now = datetime.datetime.today()
        if country_code in TIME_LIMITS \
                and now.hour >= TIME_LIMITS[country_code]:
            now = now + datetime.timedelta(days=1)

        return now.strftime(str_format)

    @staticmethod
    def get_date_range(start_date: datetime.date, end_date: datetime.date) -> list:
        date_list = []

        if isinstance(start_date, datetime.datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime.datetime):
            end_date = end_date.date()

        while start_date <= end_date:
            date_list.append(start_date)
            start_date += datetime.timedelta(days=1)
        return date_list


