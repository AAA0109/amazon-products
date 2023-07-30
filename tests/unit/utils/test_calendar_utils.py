from datetime import date, timedelta

from apps.utils.calendar_utils import Calendar


def test_get_date_range():
    start_date = date(2022, 1, 1)
    end_date = date(2022, 1, 5)
    expected_dates = [date(2022, 1, 1), date(2022, 1, 2), date(2022, 1, 3), date(2022, 1, 4), date(2022, 1, 5)]
    assert Calendar.get_date_range(start_date, end_date) == expected_dates

    start_date = date(2022, 1, 5)
    end_date = date(2022, 1, 1)
    expected_dates = []
    assert Calendar.get_date_range(start_date, end_date) == expected_dates

    start_date = date(2022, 1, 1)
    end_date = date(2022, 1, 1)
    expected_dates = [date(2022, 1, 1)]
    assert Calendar.get_date_range(start_date, end_date) == expected_dates

    start_date = date(2022, 1, 1)
    end_date = start_date - timedelta(days=1)
    expected_dates = []
    assert Calendar.get_date_range(start_date, end_date) == expected_dates
