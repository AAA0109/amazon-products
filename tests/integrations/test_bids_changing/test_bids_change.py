import os.path
from csv import DictReader

import mock
import pytest

from django.test import override_settings

from apps.ads_api.constants import SpState
from apps.ads_api.data_exchange import update_sp_bids_status
from apps.ads_api.models import Profile, Campaign, Keyword, Book, Target, RecentReportData


@pytest.fixture
def data_files():
    base_data_dir = "../../../data"
    return {
        "campaigns": os.path.join(base_data_dir, "campaigns.csv"),
        "keywords": os.path.join(base_data_dir, "keywords.csv"),
        "profiles": os.path.join(base_data_dir, "profiles.csv"),
        "report_data_keywords": os.path.join(base_data_dir, "report_data_keywords.csv"),
        "report_data_targets": os.path.join(base_data_dir, "report_data_targets.csv"),
        "books": os.path.join(base_data_dir, "books.csv"),
        "book_campaign": os.path.join(base_data_dir, "book_campaign.csv"),
        "bid_changes_keywords": os.path.join(base_data_dir, "bid_changes_keywords.csv"),
        "bid_changes_targets": os.path.join(base_data_dir, "bid_changes_targets.csv"),
        "targets": os.path.join(base_data_dir, "targets.csv"),
    }


@pytest.fixture
def expected_keyword_bid_changes(data_files):
    expected_bids_per_keywords = []
    for row in DictReader(open(data_files["bid_changes_keywords"])):
        if SpState.PAUSED not in row.values():
            row["bid"] = float(row["bid"])
        else:
            row["state"] = row.pop("bid")

        row["keywordId"] = row["keywordId"]

        expected_bids_per_keywords.append(row)
    return expected_bids_per_keywords


@pytest.fixture
def expected_targets_bid_changes(data_files):
    expected_bids_per_keywords = []
    for row in DictReader(open(data_files["bid_changes_targets"])):
        if SpState.PAUSED not in row.values():
            row["bid"] = float(row["bid"])
        else:
            row["state"] = row.pop("bid")

        row["targetId"] = row["targetId"]

        expected_bids_per_keywords.append(row)
    return expected_bids_per_keywords


@pytest.fixture
def load_keyword_data(data_files):
    keywords = []
    for row in DictReader(open(data_files["keywords"])):
        keywords.append(Keyword(**row))
    Keyword.objects.bulk_create(keywords)

    report_data_keywords = []
    for row in DictReader(open(data_files["report_data_keywords"])):
        report_data_keywords.append(RecentReportData(**row))
    RecentReportData.objects.bulk_create(report_data_keywords)


@pytest.fixture
def load_targets_data(data_files):
    targets = []
    for row in DictReader(open(data_files["targets"])):
        targets.append(Target(**row))
    Target.objects.bulk_create(targets)

    report_data_targets = []
    for row in DictReader(open(data_files["report_data_targets"])):
        report_data_targets.append(RecentReportData(**row))
    RecentReportData.objects.bulk_create(report_data_targets)


@pytest.fixture
def load_data(data_files):
    for row in DictReader(open(data_files["profiles"])):
        profile = Profile(**row)
        profile.save()

    campaigns = []
    for row in DictReader(open(data_files["campaigns"])):
        campaigns.append(Campaign(**row))
    Campaign.objects.bulk_create(campaigns)

    books = []
    for row in DictReader(open(data_files["books"])):
        books.append(Book(**row))
    Book.objects.bulk_create(books)

    book_campaign = []
    for row in DictReader(open(data_files["book_campaign"])):
        book_campaign.append(Book.campaigns.through(**row))
    Book.campaigns.through.objects.bulk_create(book_campaign)


@pytest.mark.skip(reason="Executes too long")
@pytest.mark.freeze_time("2023-02-06")
@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@mock.patch(
    "apps.ads_api.adapters.amazon_ads.sponsored_products.keywords_adapter.KeywordsAdapter.batch_update"
)
def test_keywords_bids_change(ads_update_mock, load_data, expected_keyword_bid_changes, load_keyword_data):
    update_sp_bids_status.delay([111])
    assert ads_update_mock.call_args[0][0] == expected_keyword_bid_changes


@pytest.mark.skip(reason="Executes too long")
@pytest.mark.freeze_time("2023-02-06")
@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@mock.patch("apps.ads_api.adapters.amazon_ads.sponsored_products.targets_adapter.TargetsAdapter.batch_update")
def test_targets_bids_change(ads_update_mock, load_data, expected_targets_bid_changes, load_targets_data):
    update_sp_bids_status.delay([111])
    assert ads_update_mock.call_args[0][0] == expected_targets_bid_changes
