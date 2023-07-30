import datetime

import pytest

from apps.ads_api.constants import SpReportType, ReportStatus, ServerLocation
from apps.ads_api.entities.amazon_ads.reports import ReportEntity
from apps.ads_api.models import CampaignPurpose, Book, Campaign, Profile, ProductAd, AdGroup, Keyword, Target
from apps.ads_api.repositories.book.book_repository import BookRepository
from apps.ads_api.repositories.keywords.keywords_repository import KeywordsRepository
from apps.ads_api.repositories.report_data_repository import ReportDataRepository
from apps.ads_api.repositories.targets.targets_repository import TargetsRepository


@pytest.fixture
def campaign() -> Campaign:
    return Campaign.objects.create(
        managed=True,
        campaign_id_amazon=123,
        campaign_purpose=CampaignPurpose.Discovery,
        campaign_name="ABFM-SP-Auto-Discovery-Complements-1-1801019959-Paperback"
    )


@pytest.fixture
def product_ad(campaign, ad_group) -> ProductAd:
    return ProductAd.objects.create(
        product_ad_id=1,
        campaign=campaign,
        ad_group=ad_group,
    )


@pytest.fixture
def book() -> Book:
    return Book.objects.create(
        title="test_title",
        asin="testasin",
    )


@pytest.fixture()
def profile() -> Profile:
    return Profile.objects.create(
        profile_id=1,
        entity_id=1,
        nickname="test_nickname",
        monthly_budget=10,
        research_percentage=20,
    )


@pytest.fixture
def ad_group(campaign):
    return AdGroup.objects.create(
        ad_group_id=1,
        ad_group_name="test_ad_group_name",
        campaign=campaign
    )


@pytest.fixture
def in_progress_report_entity_from_response():
    report = ReportEntity(
        **{
            "report_id": "test_report_id_1",
            "report_type": SpReportType.CAMPAIGN,
            "report_status": ReportStatus.PENDING,
            "report_server": ServerLocation.EUROPE,
            "start_date": datetime.datetime.today(),
            "end_date": datetime.datetime.today(),
        }
    )
    return report


@pytest.fixture
def report_data(campaign, profile):
    campaign.profile = profile
    campaign.save()

    return [
        ReportDataRepository.create_from_kwargs(
            date=datetime.datetime(day=29, month=1, year=2023),
            report_type=SpReportType.CAMPAIGN,
            spend=0.8,
            campaign=campaign,
        ),
        ReportDataRepository.create_from_kwargs(
            date=datetime.datetime(day=28, month=1, year=2023),
            report_type=SpReportType.CAMPAIGN,
            spend=0.2,
            campaign=campaign,
        ),
    ]


@pytest.fixture
def keywords(campaign):
    return [
        Keyword.objects.create(keyword_id=1, campaign=campaign),
        Keyword.objects.create(keyword_id=2, campaign=campaign),
    ]


@pytest.fixture
def targets(campaign):
    return [
        Target.objects.create(target_id=1, campaign=campaign),
        Target.objects.create(target_id=2, campaign=campaign),
    ]
