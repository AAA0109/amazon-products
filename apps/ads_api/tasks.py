import logging
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union

from celery import chain, group
from django.db.models import F, Q
from sp_api.api import Catalog, CatalogItems
from sp_api.base import Marketplaces

from adsdroid.celery import app
from apps.ads_api.adapters.amazon_ads.book_catalog_adapter import BookCatalogAdapter
from apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter import (
    CampaignAdapter,
)
from apps.ads_api.adapters.amazon_ads.sponsored_products.keywords_adapter import (
    KeywordsAdapter,
)
from apps.ads_api.adapters.amazon_ads.sponsored_products.negative_keywords_adapter import (
    NegativeKeywordsAdapter,
)
from apps.ads_api.adapters.amazon_ads.sponsored_products.negative_targets_adapter import (
    NegativeTargetsAdapter,
)
from apps.ads_api.adapters.amazon_ads.sponsored_products.targets_adapter import (
    TargetsAdapter,
)
from apps.ads_api.campaigns.auto_gp_campaign import AutoGPCampaign
from apps.ads_api.campaigns.broad_research_campaign import BroadResearchCampaign
from apps.ads_api.campaigns.broad_research_single_campaign import (
    BroadResearchSingleCampaign,
)
from apps.ads_api.campaigns.discovery_campaign import DiscoveryCampaign
from apps.ads_api.campaigns.exact_scale_campaign import ExactScaleCampaign
from apps.ads_api.campaigns.exact_scale_single_campaign import ExactScaleSingleCampaign
from apps.ads_api.campaigns.gp_campaign import GPCampaign
from apps.ads_api.campaigns.product.product_comp_campaign import ProductCompCampaign
from apps.ads_api.campaigns.product.product_exp_campaign import ProductExpCampaign
from apps.ads_api.campaigns.product.product_own_campaign import ProductOwnCampaign
from apps.ads_api.constants import (
    CAMPAIGN_TYPES_REQUIRED_TARGETS,
    CAMPAIGN_CREATION_SPREADSHEET_ID,
    CAMPAIGN_MAX_TARGETS_MAP,
    DEFAULT_BID,
    DEFAULT_MAX_BID,
    DEFAULT_MAX_BID_CONSERVATIVE,
    DEFAULT_REQUESTED_DATE_RANGE_FOR_REPORTS,
    MIN_BOOK_REVIEWS,
    BaseServingStatus,
    CampaignRetryStrategy,
    CampaignServingStatus,
    MatchType,
    NegativeMatchType,
    NegativeTargetingExpressionPredicateType,
    ProductAdServingStatus,
    ServerLocation,
    SpEndpoint,
    SpState,
    TargetingExpressionPredicateType,
    country_languages,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import (
    Budget,
    CampaignEntity,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.keywords import KeywordEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.negative_keyword import (
    NegativeKeywordEntity,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.negative_target import (
    NegativeTargetEntity,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.targets import (
    Expression,
    TargetEntity,
)
from apps.ads_api.exceptions.ads_api.base import (
    BaseAmazonAdsException,
    ObjectNotCreatedError,
)
from apps.ads_api.exceptions.ads_api.campaigns import (
    CampaignAlreadyExists,
    InvalidCampaignPurpose,
)
from apps.ads_api.exceptions.ads_api.product_ads import ProductAdIneligible
from apps.ads_api.google_sheets import (
    RETRY_SHEET_NAME,
    GoogleSheet,
    _process_read_values,
)
from apps.ads_api.models import (
    Book,
    Campaign,
    CampaignPurpose,
    Keyword,
    Profile,
    Target,
)
from apps.ads_api.repositories.book.book_catalog_repository import BookCatalogRepository
from apps.ads_api.repositories.book.book_repository import BookRepository
from apps.ads_api.repositories.keywords.keywords_repository import KeywordsRepository
from apps.ads_api.repositories.profile.profile_server_repository import (
    ProfileServerRepository,
)
from apps.ads_api.repositories.profile_repository import ProfileRepository
from apps.ads_api.repositories.report_data_repository import ReportDataRepository
from apps.ads_api.repositories.targets.recreate_targets_repository import (
    RecreateTargetsRepository,
)
from apps.ads_api.services.ad_groups.sync_ad_groups_service import SyncAdGroupsService
from apps.ads_api.services.ad_groups.sync_create_service import SyncCreateAdGroupService
from apps.ads_api.services.books.details_update_service import BooksDetailsService
from apps.ads_api.services.books.eligibility_service import BookElgibilityService
from apps.ads_api.services.books.update_books_eligibility_service import (
    UpdateBooksEligibilityService,
)
from apps.ads_api.services.books.update_managed_books_for_unmanaged_profiles import (
    UpdateManagedBooksForUnmanagedProfilesService,
)
from apps.ads_api.services.campaigns.build_campaign_entity_service import (
    BuildCampaignEntityService,
)
from apps.ads_api.services.campaigns.clean_up_service import CleanUpCampaignsService
from apps.ads_api.services.campaigns.recalculate_campaign_budget_service import (
    RecalculateCampaignBudgetService,
)
from apps.ads_api.services.campaigns.sync_campaigns_service import SyncCampaignsService
from apps.ads_api.services.campaigns.sync_create_service import (
    SyncCreateCampaignService,
)
from apps.ads_api.services.campaigns.sync_delete import SyncDeleteCampaignService
from apps.ads_api.services.campaigns.update_managed_campaigns_for_unmanaged_profiles import (
    UpdateManagedCampaignsForUnmanagedProfilesService,
)
from apps.ads_api.services.product_ads.sync_create_product_ads import (
    SyncCreateProductAdsService,
)
from apps.ads_api.services.product_ads.sync_product_ads_service import (
    SyncProductAdsService,
)
from apps.ads_api.services.profiles.profit_mode_service import ProfitModeService
from apps.ads_api.services.profiles.sync_profiles_service import SyncProfilesService
from apps.ads_api.services.reports.download_reports_service import (
    DownloadReportsService,
)
from apps.ads_api.services.reports.request_by_id_service import RequestReportByIdService
from apps.ads_api.services.reports.request_per_dates_service import (
    RequestPerDatesService,
)
from apps.ads_api.validators.book_validator import BookValidator
from apps.openai_api.suggesters.title_asins_suggester import TitleAsinsSuggester
from apps.openai_api.suggesters.title_keywords_suggester import TitleKeywordsSuggester
from apps.sp_api.asin_finder import ASINFinder
from apps.sp_api.book_search import BookSearch
from apps.sp_api.constants import classificationIds
from apps.sp_api.credentials import credentials
from apps.utils.celery_task_locker import CeleryTaskLocker
from apps.utils.chunks import split

_logger = logging.getLogger(__name__)


@app.task
def map_callback(callback):
    # Map a callback to all tasks and return as a group
    from apps.ads_api.data_exchange import (
        classify_ad_groups,
        fill_out_associated_sp_campaigns_in_book_model,
        get_asins_for_sp_campaigns,
        recalculate_acos,
        sp_campaign_purpose_update,
        sync_keywords,
    )

    tasks = (
        partial_request_reports.s(profile_ids=callback),
        sync_campaigns.s(profile_ids=callback),
        sync_ad_groups.s(profile_ids=callback),
        sync_product_ads.s(profile_ids=callback),
        sync_keywords.s(profile_ids=callback),
        get_profile_book_catalog.s(profile_ids=callback),
        get_asins_for_sp_campaigns.s(profile_ids=callback),
        classify_ad_groups.s(profile_ids=callback),
        sp_campaign_purpose_update.s(profile_ids=callback),
        fill_out_associated_sp_campaigns_in_book_model.s(profile_ids=callback),
        recalculate_acos.s(),
    )
    return group(tasks)()


@app.task
def partial_request_reports(profile_ids):
    max_end_date = datetime.today()
    start_date = datetime.today() - timedelta(days=95)
    profiles_ids = list(Profile.objects.filter(id__in=profile_ids).values_list("profile_id", flat=True))

    # Loop through each 30-day interval and request reports as requests cannot be longer than 31 days in range
    while start_date <= max_end_date:
        end_date = start_date + timedelta(days=30)
        if end_date > max_end_date:
            end_date = max_end_date

        # Request the service
        service = RequestPerDatesService(start_date=start_date, end_date=end_date, managed_profiles_ids=profiles_ids)
        service.request()

        # Increment the start_date by 1 day for the next iteration
        start_date = end_date + timedelta(days=1)


# PROFILES
@app.task
def sync_profiles(
    server: Optional[List[ServerLocation]] = None,
) -> Union[list[int], None]:
    """
    Returns new created profiles ids
    """
    _logger.info("sync_profiles is started")
    sync_service = SyncProfilesService(server_location=server)
    ids = sync_service.sync()
    _logger.info("sync_profiles is complete")
    return ids


@app.task
def sync_profiles_chain():
    """
    Starts chain for new profiles
    """
    _logger.info("sync_profiles_chain started")
    (sync_profiles.s() | map_callback.s())()
    _logger.info("sync_profiles_chain is complete")


# REPORTS
@app.task
def sp_request_reports(
    managed_profiles_ids: list[int],
    start_date: str,
    end_date: str,
    seconds_sleep_after_complete: int = None,
):
    _logger.info("sp_request_reports is started")
    time_formats = ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")
    for time_format in time_formats:
        try:
            start_date = datetime.strptime(start_date, time_format)
            end_date = datetime.strptime(end_date, time_format)
        except ValueError:
            pass
        else:
            break
    else:
        raise ValueError(f"Not supported data type for {str(start_date)}")

    if managed_profiles_ids:
        service = RequestPerDatesService(
            start_date=start_date,
            end_date=end_date,
            managed_profiles_ids=managed_profiles_ids,
        )
        service.request()
    else:
        _logger.info("No profile ids were passed")
    if seconds_sleep_after_complete:
        _logger.info("All reports are requested. Sleeping for %s", seconds_sleep_after_complete)
        time.sleep(seconds_sleep_after_complete)
    _logger.info("sp_request_reports is complete")


@app.task
def request_reports_by_ids(report_ids: list[str]):
    request_service = RequestReportByIdService()
    request_service.request(report_ids)


@app.task
def sp_process_reports():
    _logger.info("sp_process_reports is started")
    service = DownloadReportsService()
    service.download()
    _logger.info("sp_process_reports is complete")


@app.task
def sp_data_sync_all():
    # Run all reports for all managed profiles for 2 days ago
    end_date = datetime.today()
    start_date = end_date - timedelta(days=2)
    managed_profiles_ids = ProfileRepository.get_managed_profiles_ids()
    service = RequestPerDatesService(
        managed_profiles_ids=managed_profiles_ids,
        start_date=start_date,
        end_date=end_date,
    )
    service.request()


@app.task
def report_chain(profiles_ids: int):
    """Helper Celery chaining task to request and download reports from Amazon"""
    _logger.info("report_chain is started")

    end_date = datetime.today()
    start_date = end_date - timedelta(days=3)

    tasks = (
        sp_request_reports.si(
            start_date=start_date,
            end_date=end_date,
            managed_profiles_ids=profiles_ids,
            seconds_sleep_after_complete=1800,
        )
        | sp_process_reports.si()
    )
    chain(tasks).apply_async()
    _logger.info("report_chain is complete")


@app.task
def transfer_90_days_recent_report_data_to_report_data():
    ReportDataRepository.transfere_90_days_recent_report_data_to_report_data()


@app.task
def sync_sp_data(server_locations: list[ServerLocation]):
    _logger.info("sync_sp_data is started")
    from apps.ads_api.data_exchange import (
        reset_gp_bids,
        udpate_sp_placements,
        update_sp_bids_status,
    )

    profile_ids = []
    profile_pks = []
    for location in server_locations:
        profile_server_repo = ProfileServerRepository(location)
        profile_ids += profile_server_repo.get_profile_ids_list()
        profile_pks += profile_server_repo.get_primary_keys_list()

    post_reports_tasks = (
        udpate_sp_placements.si(profile_pks),
        reset_gp_bids.si(profile_pks),
        # process_sp_queries.si(profile_pks),
    )

    split_pks = list(split(profile_pks, 4))

    tasks = (
        sp_request_reports.si(
            start_date=datetime.today() - timedelta(days=DEFAULT_REQUESTED_DATE_RANGE_FOR_REPORTS),
            end_date=datetime.today(),
            managed_profiles_ids=profile_ids,
            seconds_sleep_after_complete=1800,
        )
        | sp_request_reports.si(
            start_date=datetime.today() - timedelta(days=30),
            end_date=datetime.today() - timedelta(days=30),
            managed_profiles_ids=profile_ids,
        )
        | sp_process_reports.si()
        | update_sp_bids_status.si(split_pks[0])
        | update_sp_bids_status.si(split_pks[1])
        | update_sp_bids_status.si(split_pks[2])
        | update_sp_bids_status.si(split_pks[3])
        | group(post_reports_tasks)
    )

    chain(tasks).apply_async()
    _logger.info("sync_sp_data is complete")


@app.task
def cleanup_managed_books_and_campaigns_for_unmanaged_profiles():
    profile_pks = ProfileRepository.get_unmanaged_profiles_pks()
    UpdateManagedCampaignsForUnmanagedProfilesService.update(profile_pks)
    UpdateManagedBooksForUnmanagedProfilesService.update(profile_pks)


# BOOKS
@app.task
def get_profile_book_catalog(profile_ids: Optional[list[int]] = None):
    """Gets books for managed profiles from the Amazon Ads console catalog"""
    with CeleryTaskLocker(lock_expire=20, lock_id=get_profile_book_catalog.__name__, oid=app.oid) as acquired:
        if acquired:
            time.sleep(15)
            _logger.info("Task executed. no lock found")
            if profile_ids:
                profiles = Profile.objects.filter(id__in=profile_ids)
            else:
                profiles = ProfileRepository.get_managed_profiles()

            for profile in profiles:
                book_catalog_adapter = BookCatalogAdapter(profile.entity_id, profile.country_code)

                book_catalog = book_catalog_adapter.retrieve_book_catalog()
                if len(book_catalog) == 0:
                    profiles = Profile.objects.filter(nickname=profile.nickname, country_code__in=["US", "CA"])
                    for additional_market_profile in profiles:
                        book_catalog_adapter = BookCatalogAdapter(
                            additional_market_profile.entity_id,
                            additional_market_profile.country_code,
                        )
                        book_catalog = book_catalog_adapter.retrieve_book_catalog()
                        if len(book_catalog) > 0:
                            _logger.info(
                                f"Got {len(book_catalog)} books for profile: {profile} "
                                f"from {additional_market_profile.country_code} market."
                            )
                            break

                book_catalog_repo = BookCatalogRepository(book_profile=profile, book_catalog=book_catalog)
                book_catalog_repo.save_books_to_profile()

                _logger.info(f"Got {len(book_catalog)} books for profile: {profile}")

            return
    _logger.info("get_profile_book_catalog is already being imported by another worker")


@app.task
def update_books_details(books_to_process_ids: Optional[list[int]] = None):
    books_details = BooksDetailsService(books_to_process_ids)
    books_details.update_books_details()


@app.task
def set_books_managed_status():
    _logger.info("update_books_managed_status started")
    books = BookRepository.get_books_to_be_managed()
    BookRepository.batch_update_from_kwargs(books, managed=True)
    _logger.info("update_books_managed_status is complete")


@app.task
def update_books_eligibility():
    service = UpdateBooksEligibilityService()
    service.update()


# CAMPAIGNS


@app.task
def update_profit_campaign_budgets():
    """Increases the budget of out of budget campaigns if they've been performing well"""
    profiles_with_out_budget_campaigns = Profile.objects.filter(
        campaigns__serving_status=BaseServingStatus.CAMPAIGN_OUT_OF_BUDGET.value,
        managed=True,
        campaigns__managed=True,
    ).distinct("profile_id")

    for profile in profiles_with_out_budget_campaigns:
        campaigns_out_budget = Campaign.objects.filter(
            serving_status=BaseServingStatus.CAMPAIGN_OUT_OF_BUDGET.value,
            profile=profile,
            managed=True,
            sponsoring_type="sponsoredProducts",
        )

        campaigns_to_update = []
        for campaign in campaigns_out_budget:
            recalculate_budget_service = RecalculateCampaignBudgetService(campaign)
            new_budget = recalculate_budget_service.recalculate_budget()
            if campaign.daily_budget != new_budget:
                campaigns_to_update.append(
                    CampaignEntity(
                        external_id=campaign.campaign_id_amazon,
                        budget=Budget(budget=new_budget, budget_type="DAILY"),
                    ).dict(exclude_none=True, by_alias=True)
                )

        if len(campaigns_to_update) > 0:
            campaign_adapter = CampaignAdapter(profile)
            updated, errors = campaign_adapter.batch_update(campaigns_to_update)

            if errors:
                _logger.error(
                    "Some campaigns were not updated. Updated [%s], errors [%s]",
                    updated,
                    errors,
                )
                raise BaseAmazonAdsException(
                    "Some campaigns were not updated. To see additional information, please "
                    f"refer to the logs. Time - {datetime.now()}"
                )

            _logger.info(
                f"Updated {len(updated)}/{campaigns_to_update}"
                f" campaign budgets on {profile.nickname}"
                f" [{profile.country_code}]"
            )


@app.task
def campaign_clean_up():
    """Pauses managed campaigns with invalid ad groups or product ads"""
    CleanUpCampaignsService.clean_up()


@app.task
def sync_campaigns(profile_ids: Optional[list[int]] = None):
    """Sync high level campaign data for managed profiles

    :param profile_ids: primary keys of profiles. If no IDs
    were given, primary keys of all managed profiles would be taken to process.
    """

    sync_campaigns_service = SyncCampaignsService(profile_ids)
    sync_campaigns_service.sync()


@app.task
def sync_ad_groups(profile_ids: Optional[list[int]] = None):
    """Sync high level ad group data for managed profiles

    :param profile_ids: primary keys of profiles. If no IDs
    were given, primary keys of all managed profiles would be taken to process.
    """

    sync_ad_groups_service = SyncAdGroupsService(profile_ids)
    sync_ad_groups_service.sync()


class PostCreateCampaignSync:
    @classmethod
    def sync(cls, profile_ids):
        sync_campaigns(profile_ids=profile_ids)
        sync_ad_groups(profile_ids=profile_ids)
        sync_product_ads(profile_ids=profile_ids)
        from apps.ads_api.data_exchange import sync_keywords

        sync_keywords(endpoint=SpEndpoint.KEYWORDS, profile_ids=profile_ids)
        sync_keywords(endpoint=SpEndpoint.TARGETS, profile_ids=profile_ids)
        from apps.ads_api.data_exchange import get_asins_for_sp_campaigns

        get_asins_for_sp_campaigns(profile_ids=profile_ids)
        from apps.ads_api.data_exchange import sp_campaign_purpose_update

        sp_campaign_purpose_update(profile_ids=profile_ids)


@app.task
def create_campaign_from_google_sheet():
    """Creates campaigns as a result of reading 1 column's data"""
    with CeleryTaskLocker(lock_expire=3600 * 5, lock_id=get_profile_book_catalog.__name__, oid=app.oid) as acquired:
        if acquired:
            profiles_per_country: Dict[str, set[str]] = defaultdict(set)
            google_sheet = GoogleSheet()
            sheet_instance = google_sheet._get_sheet_object_by_key(worksheet_key=CAMPAIGN_CREATION_SPREADSHEET_ID)
            new_campaign_info_list = google_sheet.get_new_campaign_info(spreadsheet=sheet_instance)
            if len(new_campaign_info_list) < 3:
                _logger.info("No new campaigns info found in Google Sheet inputs.")
                return

            new_campaign_info_dict = _process_read_values(values_from_sheet=new_campaign_info_list)
            asin = new_campaign_info_dict["asin"]
            campaign_type = new_campaign_info_dict.get("type")
            targets = new_campaign_info_dict.get("targets")
            updated_books = []
            while len(asin) > 1:
                _logger.info("new_campaign_info_list %s", new_campaign_info_list)
                if len(new_campaign_info_list) < 5:
                    # fill new_campaign_info_list with blank strings to prevent index out of range error
                    actual_length = len(new_campaign_info_list)
                    count_mismatch = 5 - actual_length
                    new_campaign_info_list.extend("" for _ in range(count_mismatch))
                    _logger.info(
                        "new_campaign_info_list %s, count=%s",
                        new_campaign_info_list,
                        len(new_campaign_info_list),
                    )
                if campaign_type in CAMPAIGN_TYPES_REQUIRED_TARGETS and targets is None:
                    _logger.error(
                        "Targets was not provided for %s, please check input in Google Sheet.",
                        campaign_type
                    )
                    new_campaign_info_list[
                        4
                    ] = f"Failed: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}, details: Targets not provided for Type: {campaign_type}"
                    # move data from input to retry sheet
                    google_sheet.move_created_campaign_to_output(
                        campaign_info=new_campaign_info_list,
                        spreadsheet=sheet_instance,
                        write_sheet_name=RETRY_SHEET_NAME,
                    )
                else:
                    if len(asin) != 10:
                        _logger.error(
                            "Length of ASIN: %s was not 10, please check input in Google Sheet.",
                            asin,
                        )
                        _logger.info(
                            "new_campaign_info_list %s, count=%s",
                            new_campaign_info_list,
                            len(new_campaign_info_list),
                        )
                        if len(new_campaign_info_list) < 5:
                            # fill new_campaign_info_list with blank strings to prevent index out of range error
                            actual_length = len(new_campaign_info_list)
                            count_mismatch = 5 - actual_length
                            new_campaign_info_list.extend("" for _ in range(count_mismatch))
                            _logger.info(
                                "new_campaign_info_list %s, count=%s",
                                new_campaign_info_list,
                                len(new_campaign_info_list),
                            )

                        new_campaign_info_list[
                            4
                        ] = f"Failed: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}, details: Length of ASIN: {asin} was not 10"
                        # move data from input to retry sheet
                        google_sheet.move_created_campaign_to_output(
                            campaign_info=new_campaign_info_list,
                            spreadsheet=sheet_instance,
                            write_sheet_name=RETRY_SHEET_NAME,
                        )

                    # create new campaigns
                    book = (
                        Book.objects.filter(profile__country_code=new_campaign_info_dict["country_code"], asin=asin)
                        .select_related("profile")
                        .first()
                    )

                    if book and book.id not in updated_books:
                        book_eligibility_service = BookElgibilityService(book)
                        book_eligibility_service.refresh()
                        updated_books.append(book.id)

                    book_validator = BookValidator(book)

                    if book_validator.is_valid():
                        _logger.info("new_campaign_info_list values: %s", new_campaign_info_list)
                        profile = book.profile
                        # save nicknames of profiles for later sync of campaigns and targets & keywords
                        profiles_per_country[profile.country_code].add(profile.nickname)
                        campaign_purpose = new_campaign_info_dict.get("type")
                        bid = (
                            float(new_campaign_info_dict["bid"])
                            if "bid" in new_campaign_info_dict and len(new_campaign_info_dict["bid"]) > 0
                            else DEFAULT_BID
                        )
                        keywords = new_campaign_info_dict.get("targets")
                        from apps.ads_api.factories.compaign_factory import CampaignFactory

                        campaign_factory = CampaignFactory(book=book, keywords=keywords, default_bid=bid)

                        try:
                            campaign = campaign_factory.choose_campaign_type(campaign_purpose)
                        except InvalidCampaignPurpose:
                            google_sheet.correct_campaign_purpose(spreadsheet=sheet_instance)
                            _logger.info("Campaign purpose invalid. Exiting...")
                            return

                        try:
                            campaign.create()
                        except (ProductAdIneligible, CampaignAlreadyExists) as e:
                            _logger.info(
                                "new_campaign_info_list %s, count=%s",
                                new_campaign_info_list,
                                len(new_campaign_info_list),
                            )
                            if len(new_campaign_info_list) < 5:
                                # fill new_campaign_info_list with blank strings to prevent index out of range error
                                actual_length = len(new_campaign_info_list)
                                count_mismatch = 5 - actual_length
                                new_campaign_info_list.extend("" for _ in range(count_mismatch))
                                _logger.info(
                                    "new_campaign_info_list %s, count=%s",
                                    new_campaign_info_list,
                                    len(new_campaign_info_list),
                                )

                            new_campaign_info_list[
                                4
                            ] = f"Failed: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}, details: {e}"
                            # move data from input to retry sheet
                            google_sheet.move_created_campaign_to_output(
                                campaign_info=new_campaign_info_list,
                                spreadsheet=sheet_instance,
                                write_sheet_name=RETRY_SHEET_NAME,
                            )
                        except (BaseAmazonAdsException, Exception) as e:
                            _logger.info(
                                "new_campaign_info_list %s, count=%s",
                                new_campaign_info_list,
                                len(new_campaign_info_list),
                            )
                            if len(new_campaign_info_list) < 5:
                                # fill new_campaign_info_list with blank strings to prevent index out of range error
                                actual_length = len(new_campaign_info_list)
                                count_mismatch = 5 - actual_length
                                new_campaign_info_list.extend("" for _ in range(count_mismatch))
                                _logger.info(
                                    "new_campaign_info_list pulled %s",
                                    new_campaign_info_list,
                                    len(new_campaign_info_list),
                                )

                            new_campaign_info_list[
                                4
                            ] = f"Failed: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}, details: {e}"
                            # move data from input to retry sheet
                            google_sheet.move_created_campaign_to_output(
                                campaign_info=new_campaign_info_list,
                                spreadsheet=sheet_instance,
                                write_sheet_name=RETRY_SHEET_NAME,
                            )
                            _logger.error("Campaign was not created, issue - %s", e)
                            raise BaseAmazonAdsException(f"Campaign was not created, issue - {e}")
                        else:
                            # add created timestamp information to the info to be moved
                            while len(new_campaign_info_list) < 5:
                                new_campaign_info_list.append("")

                            new_campaign_info_list[4] = f"Created: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}"
                            # move data from input to output sheet
                            google_sheet.move_created_campaign_to_output(
                                campaign_info=new_campaign_info_list, spreadsheet=sheet_instance
                            )

                    elif book is None:
                        _logger.error("Book with asin - %s not in DB! Writing into retry sheet..", asin)
                        google_sheet.move_created_campaign_to_output(
                            campaign_info=new_campaign_info_list,
                            spreadsheet=sheet_instance,
                            write_sheet_name=RETRY_SHEET_NAME,
                        )
                    elif not book.eligible:
                        new_campaign_info_list[4] = "Failed: Book %s is not eligible for advertising!" % asin
                        _logger.error(
                            "Book with asin - %s is not eligible for advertising!" " Writing into the output sheet..",
                            asin,
                        )
                        google_sheet.move_created_campaign_to_output(
                            campaign_info=new_campaign_info_list,
                            spreadsheet=sheet_instance,
                        )
                    elif book.profile.accessible is False:
                        new_campaign_info_list[4] = "Failed: Book %s profile is not accessible!" % asin
                        _logger.error(
                            "Book with asin - %s profile is not accessible!" " Writing into the output sheet..",
                            asin,
                        )
                        google_sheet.move_created_campaign_to_output(
                            campaign_info=new_campaign_info_list,
                            spreadsheet=sheet_instance,
                        )
                    elif not book.title:
                        _logger.error(
                            "Book with the asin %s has empty title! Writing into the retry sheet..",
                            asin,
                        )
                        google_sheet.move_created_campaign_to_output(
                            campaign_info=new_campaign_info_list,
                            spreadsheet=sheet_instance,
                            write_sheet_name=RETRY_SHEET_NAME,
                        )

                # fetch new data to possibly start another loop
                new_campaign_info_list = google_sheet.get_new_campaign_info(spreadsheet=sheet_instance)
                if len(new_campaign_info_list) < 3:
                    break
                new_campaign_info_dict = _process_read_values(values_from_sheet=new_campaign_info_list)
                asin = new_campaign_info_dict["asin"]
                campaign_type = new_campaign_info_dict.get("type")
                targets = new_campaign_info_dict.get("targets")
                # Preventive sleep to avoid throttling
                time.sleep(10)
            _logger.info("Campaigns successfully created using Google Sheet inputs. Syncing profiles and targets")
            if len(profiles_per_country) == 0:
                return
            # sync with Amazon to ensure no immediate duplication takes place
            for country_code, nicknames in profiles_per_country.items():
                profile_ids = Profile.objects.filter(nickname__in=nicknames, country_code=country_code).values_list("id")

                post_sync = PostCreateCampaignSync()
                post_sync.sync(profile_ids)
            _logger.info("Syncing of profiles and targets etc. complete.")
            return
    _logger.warning("%s is already being imported by another worker", create_campaign_from_google_sheet.__name__)

# PRODUCT ADS


@app.task
def sync_product_ads(profile_ids: Optional[list[int]] = None):
    """Sync high level product ad data for managed profiles"""

    if profile_ids:
        profiles = Profile.objects.filter(id__in=profile_ids)
    else:
        profiles = Profile.objects.filter(managed=True)

    for profile in profiles:
        sync_product_ads_service = SyncProductAdsService(profile)
        sync_product_ads_service.sync()
        # _logger.info(f"Synced product ads for profile {profile}") # Duplicate log, also shows up as sync_product_ads_service.py:67


@app.task
def turn_on_profit_mode(profile_ids: list[int]):
    """Turns on profit mode on a profile, focusing only on targets with sales. Turns all sales=0 to MIN_BID"""
    profiles = ProfileRepository.retrieve_profiles_by_ids(profile_ids)
    for profile in profiles:
        ProfitModeService.turn_on(profile)


class RetryServiceForCampaignsWithInvalidStatus:
    def __init__(self, profiles: list[Profile]) -> None:
        self._profiles = profiles
        self._created_campaigns_external_ids: list[str] = []

    campaign_serving_statuses_to_retry = [
        CampaignServingStatus.OTHER,
        CampaignServingStatus.CAMPAIGN_INCOMPLETE,
    ]

    product_ad_serving_statuses_to_retry = [
        ProductAdServingStatus.AD_MISSING_DECORATION,
        ProductAdServingStatus.AD_POLICING_SUSPENDED,
    ]

    keyword_type_campaign_purposes = [
        CampaignPurpose.Exact_Scale_Single,
        CampaignPurpose.Exact_Scale,
        CampaignPurpose.Broad_Research_Single,
        CampaignPurpose.Broad_Research,
        CampaignPurpose.GP,
    ]

    target_type_campaign_purposes = [
        CampaignPurpose.Discovery_Loose_Match,
        CampaignPurpose.Discovery_Close_Match,
        CampaignPurpose.Discovery_Substitutes,
        CampaignPurpose.Discovery_Complements,
        CampaignPurpose.Discovery,
        CampaignPurpose.Product_Comp,
        CampaignPurpose.Product_Own,
        CampaignPurpose.Product_Self,
    ]

    def retry(self):
        for profile in self._profiles:
            invalid_campaigns = self._retrieve_invalid_campaigns(profile)
            _logger.info(
                "Campaigns with invalid serving status retrieved: %s, for profile: %s",
                invalid_campaigns,
                profile,
            )
            campaigns_to_be_post_processed = []

            try:
                for campaign in invalid_campaigns:
                    strategy = self._resolve_retry_strategy(campaign)
                    if strategy == CampaignRetryStrategy.RECREATE:
                        self._recreate_campaign(campaign)
                        campaigns_to_be_post_processed.append(campaign)
                    elif strategy == CampaignRetryStrategy.FILL_UP_WITH_KEYWORDS:
                        self._fill_campaign_with_keywords(campaign)
                    else:
                        raise NotImplemented(f"Not implemented retry strategy {strategy}")

            except Exception as e:
                _logger.error(e)
            finally:
                self._post_recreate_actions(campaigns_to_be_post_processed, profile)

            self._created_campaigns_external_ids.clear()

    def _post_recreate_actions(self, campaigns: list[dict], profile: Profile):
        self._sync_delete_campaigns(campaigns, profile)
        self._increase_campaigns_retry_counter()

    def _sync_delete_campaigns(self, campaigns: list[dict], profile: Profile):
        sync_delete_campaign_service = SyncDeleteCampaignService(profile)
        sync_delete_campaign_service._sync_delete_campaigns([campaign["campaign_id_amazon"] for campaign in campaigns])

    def _increase_campaigns_retry_counter(self):
        updated_count = Campaign.objects.filter(campaign_id_amazon__in=self._created_campaigns_external_ids).update(
            creation_retries_count=F("creation_retries_count") + 1
        )
        _logger.info("Campaigns creation_retries_count increased for %s campaigns", updated_count)

    def _retrieve_invalid_campaigns(self, profile: Profile):
        return Campaign.objects.filter(
            Q(serving_status__in=self.campaign_serving_statuses_to_retry)
            | Q(product_ads__serving_status__in=self.product_ad_serving_statuses_to_retry),
            creation_retries_count__lt=5,
            state=SpState.ENABLED.value,
            profile=profile,
        ).values(
            "campaign_id_amazon",
            "campaign_name",
            "serving_status",
            "campaign_purpose",
            "bidding_strategy",
            "placement_tos_mult",
            "placement_pp_mult",
            "id",
            "ad_groups__default_bid",
            "ad_groups__ad_group_id",
            "product_ads__product_ad_id",
            "product_ads__serving_status",
            "product_ads__asin",
            "profile__country_code",
            "books",
        )

    def _resolve_retry_strategy(self, campaign: dict) -> CampaignRetryStrategy:
        product_ad_serving_status = campaign["product_ads__serving_status"]

        _logger.info("Campaign serving status is %s", campaign["serving_status"])
        _logger.info("ProductAd serving status is %s", product_ad_serving_status)

        if campaign["serving_status"] == CampaignServingStatus.CAMPAIGN_INCOMPLETE.value:
            strategy = CampaignRetryStrategy.FILL_UP_WITH_KEYWORDS
        elif campaign["serving_status"] in [CampaignServingStatus.OTHER.value] or product_ad_serving_status in [
            status.value for status in self.product_ad_serving_statuses_to_retry
        ]:
            strategy = CampaignRetryStrategy.RECREATE
        else:
            raise ValueError(
                f"Unexpected campaign serving status {campaign['serving_status']}. "
                f"Allowed {self.product_ad_serving_statuses_to_retry + self.campaign_serving_statuses_to_retry}"
            )

        _logger.info("Campaign strategy resolved %s", strategy)
        return strategy

    def _recreate_campaign(self, campaign: dict):
        _logger.info("Recreating of campaign %s", campaign)
        keywords: list[dict] = []
        targets: list[dict] = []

        purpose = campaign["campaign_purpose"]
        _logger.info("Campaign purpose %s", purpose)

        if campaign.get("books"):
            book = Book.objects.get(id=campaign["books"])
        else:
            book = Book.objects.get(
                asin=campaign["product_ads__asin"],
                profile__country_code=campaign["profile__country_code"],
            )
        _logger.info("Related book %s", book)

        if purpose in self.keyword_type_campaign_purposes:
            keywords.extend(
                list(
                    Keyword.objects.filter(
                        campaign_id=campaign["id"],
                        ad_group_id=campaign["ad_groups__ad_group_id"],
                    ).values("keyword_text", "match_type")
                )
            )
            _logger.info("Retrieved keywords %s", keywords)
        elif purpose in self.target_type_campaign_purposes:
            targets.extend(
                list(
                    Target.objects.filter(
                        campaign_id=campaign["id"],
                        ad_group_id=campaign["ad_groups__ad_group_id"],
                    ).values(
                        "resolved_expression_text",
                        "resolved_expression_type",
                        "targeting_type",
                    )
                )
            )
            _logger.info("Retrieved targets %s", targets)
        elif purpose in [CampaignPurpose.Auto_GP]:
            pass
        else:
            raise TypeError(f"Unexpected campaign purpose: {purpose}")

        self._create_campaign(book, campaign, keywords, targets)

    def _create_campaign(
        self,
        book: Book,
        campaign: dict,
        keywords: Optional[list[dict]] = None,
        targets: Optional[list[dict]] = None,
    ):
        targets_adapter = TargetsAdapter(book.profile)
        negative_targets_adapter = NegativeTargetsAdapter(book.profile)
        keywords_adapter = KeywordsAdapter(book.profile)
        negative_keywords_adapter = NegativeKeywordsAdapter(book.profile)

        build_campaign_service = BuildCampaignEntityService(
            campaign_purpose=campaign["campaign_purpose"],
            book=book,
            bidding_strategy=campaign["bidding_strategy"],
            tos=campaign["placement_tos_mult"],
            pp=campaign["placement_pp_mult"],
        )
        campaign_entity = build_campaign_service.build()
        _logger.info(f"Generated campaign entity for request: {campaign_entity}")

        sync_create_campaign_service = SyncCreateCampaignService(book)
        campaign_entity = sync_create_campaign_service.create_campaign(campaign_entity)
        _logger.info(f"External created campaign: {campaign_entity}")

        sync_create_ad_group_service = SyncCreateAdGroupService(book)
        ad_group_entity = sync_create_ad_group_service.create_ad_group(
            campaign_entity, campaign["ad_groups__default_bid"]
        )
        _logger.info(f"External created ad group: {ad_group_entity}")

        sync_create_product_ad_service = SyncCreateProductAdsService(book)
        product_ad = sync_create_product_ad_service.create_product_ad(ad_group_entity)
        _logger.info(f"External created product ad: {product_ad}")

        keywords_to_create: list[dict] = []
        negative_keywords_to_create: list[dict] = []
        positive_match_type = [match_type.value for match_type in MatchType]
        negative_match_type = [match_type.value for match_type in NegativeMatchType]
        if keywords:
            for keyword in keywords:
                if keyword["match_type"] in positive_match_type:
                    keywords_to_create.append(
                        KeywordEntity(
                            campaign_id=campaign_entity.external_id,
                            ad_group_id=ad_group_entity.external_id,
                            keyword_text=keyword["keyword_text"],
                            bid=campaign["ad_groups__default_bid"],
                            state=SpState.ENABLED,
                            match_type=keyword["match_type"],
                        ).dict(exclude_none=True, by_alias=True)
                    )
                elif keyword["match_type"] in negative_match_type:
                    negative_keywords_to_create.append(
                        NegativeKeywordEntity(
                            campaign_id=campaign_entity.external_id,
                            ad_group_id=ad_group_entity.external_id,
                            keyword_text=keyword["keyword_text"],
                            bid=campaign["ad_groups__default_bid"],
                            state=SpState.ENABLED,
                            match_type=keyword["match_type"],
                        ).dict(exclude_none=True, by_alias=True)
                    )
                else:
                    raise ValueError(
                        f"Unexpected match type {keyword['match_type']}, possible types: {positive_match_type + negative_match_type}"
                    )
            created, errors = keywords_adapter.batch_create(keywords_to_create)
            _logger.info(f"External created keyords: {created}, errors {errors}")

            created, errors = negative_keywords_adapter.batch_create(negative_keywords_to_create)
            _logger.info(f"External created negative keyords: {created}, errors {errors}")

        targets_to_create: list[dict] = []
        negative_targets_to_create: list[dict] = []
        positive_predicate_types = [predicate_type.value for predicate_type in TargetingExpressionPredicateType]
        negative_predicate_types = [predicate_type.value for predicate_type in NegativeTargetingExpressionPredicateType]
        if targets:
            for target in targets:
                if target["match_type"] in positive_predicate_types:
                    targets_to_create.append(
                        TargetEntity(
                            campaign_id=campaign_entity.external_id,
                            ad_group_id=ad_group_entity.external_id,
                            bid=campaign["ad_groups__default_bid"],
                            state=SpState.ENABLED,
                            expression=[
                                Expression(
                                    type=target["resolved_expression_text"],
                                    value=target["resolved_expression_type"],
                                )
                            ],
                            expression_type=target["targeting_type"],
                        ).dict(exclude_none=True, by_alias=True)
                    )
                elif target["match_type"] in negative_predicate_types:
                    negative_targets_to_create.append(
                        NegativeTargetEntity(
                            campaign_id=campaign_entity.external_id,
                            ad_group_id=ad_group_entity.external_id,
                            bid=campaign["ad_groups__default_bid"],
                            state=SpState.ENABLED,
                            expression=[
                                Expression(
                                    type=target["resolved_expression_text"],
                                    value=target["resolved_expression_type"],
                                )
                            ],
                            expression_type=target["targeting_type"],
                        ).dict(exclude_none=True, by_alias=True)
                    )
                else:
                    raise ValueError(
                        f"Unexpected predicate type {target['match_type']}, possible types: {positive_predicate_types + negative_predicate_types}"
                    )
            created, errors = targets_adapter.batch_create(targets_to_create)
            _logger.info(f"External created targets: {created}, errors {errors}")

            created, errors = negative_targets_adapter.batch_create(negative_targets_to_create)
            _logger.info(f"External created negative targets: {created}, errors {errors}")

        if campaign_entity.external_id:
            self._created_campaigns_external_ids.append(campaign_entity.external_id)

    def _fill_campaign_with_keywords(self, campaign: dict):
        book = Book.objects.get(id=campaign["books"])
        purpose = campaign["campaign_purpose"]
        _logger.info("Campaign purpose: %s", purpose)
        _logger.info("Book: %s", book)

        if purpose in self.keyword_type_campaign_purposes:
            keywords = KeywordsRepository.retrieve_keywords_to_recreate(campaign)
            _logger.info("Keywords from db to recreate %s", keywords)

            keywords_adapter = KeywordsAdapter(book.profile)
            created, errors = keywords_adapter.batch_create(keywords)
            _logger.info("External created keywords: %s, errors: %s", created, errors)

            if created:
                KeywordsRepository.save_keywords_from_amazon(created, keywords)

            if errors:
                if "duplicateValueError" not in errors[0].values():
                    raise ObjectNotCreatedError(errors)

        elif purpose in self.target_type_campaign_purposes:
            targets = RecreateTargetsRepository.retrieve_targets_to_recraete(campaign)
            _logger.info("Targets to recreate: %s", targets)

            targets_adapter = TargetsAdapter(book.profile)
            created, errors = targets_adapter.batch_create(targets)

            if errors:
                if (
                    "duplicateValueError" not in errors[0].values()
                    or "targetingClauseSetupError" not in errors[0].values()
                ):
                    raise ObjectNotCreatedError(errors)
        else:
            raise TypeError(f"Unexpected campaign purpose: {purpose}")


@app.task
def retry_campaigns_with_invalid_serving_status(profile_pks: list[int]):
    profiles = Profile.objects.filter(id__in=profile_pks)
    retry_service = RetryServiceForCampaignsWithInvalidStatus(profiles)
    retry_service.retry()


@app.task
def update_books_launch_status():
    outdated_books = Book.objects.filter(publication_date__lt=datetime.today() - timedelta(days=60), launch=True)
    _logger.info("%s books to update launch status to False", outdated_books.count())

    updated_count = outdated_books.update(launch=False)
    _logger.info("%s books updated", updated_count)


@app.task
def create_campaigns_task(book_pks: List[int], campaign_types: Optional[tuple[CampaignPurpose]] = None):
    """
    This function creates different types of campaigns for books using ChatGPT and SP API.

    It takes as input a list of book primary keys (book_pks) and an optional tuple of CampaignPurpose enums
    (campaign_types). If no campaign_types are provided, campaigns of all types are created.

    This function supports the following types of campaigns, indicated by the CampaignPurpose enum:
    1. Broad_Research: creates a broad research campaign.
    2. Broad_Research_Single: creates a broad research campaign with single keywords.
    3. Exact_Scale: creates an exact scale campaign.
    4. Exact_Scale_Single: creates an exact scale campaign with single keywords.
    5. Product_Comp: creates a product comparison campaign.
    6. Product_Exp: creates a product experience campaign.
    7. GP: creates a general purpose campaign.
    8. Auto_GP: creates an automatic general purpose campaign.
    9. Discovery: creates a discovery campaign.

    Each campaign involves keyword suggestion, logging, campaign creation, and exception handling.
    The function logs information about the book, keywords used, and the campaigns created.
    In case of any error during campaign creation, the exception is logged, but the function continues with
    the creation of the next campaign or the next book.
    At the end of the function, a summary of all created campaigns is logged.

    Args:
        book_pks (List[int]): A list of primary keys identifying the books.
        campaign_types (Optional[tuple[CampaignPurpose]]): An optional tuple of campaign types.
            If not provided, all types of campaigns are created.

    Raises:
        Exception: Any exception raised during campaign creation is caught and logged, but does not
            interrupt the function.
    """
    from apps.ads_api.data_exchange import (
        get_asins_for_product_own_campaign
    )

    if campaign_types is None:
        campaign_types = [p for p in CampaignPurpose]
    for book_pk in book_pks:
        try:
            book: Book = Book.objects.get(id=book_pk)
        except Book.DoesNotExist:
            continue
        if book.reviews is not None and book.reviews < MIN_BOOK_REVIEWS:
            bid = DEFAULT_MAX_BID_CONSERVATIVE
        else:
            bid = DEFAULT_BID
        native_language = country_languages[book.profile.country_code]
        campaigns_created: list[str] = []
        _logger.info("Book: %s", book)

        try:
            if CampaignPurpose.Broad_Research in campaign_types:
                broad_keywords: list[str] = TitleKeywordsSuggester.suggest_keywords(
                    title=book.title, keywords_type="broad", language=native_language
                )
                _logger.info("Broad keywords: %s", broad_keywords)
                broad_research_campaign = BroadResearchCampaign(
                    book=book, text_keywords=broad_keywords, default_bid=bid
                )
                broad_research_campaign.create()
                campaigns_created.append(broad_research_campaign.__class__.__name__)
            if CampaignPurpose.Broad_Research_Single in campaign_types:
                single_keywords: list[str] = TitleKeywordsSuggester.suggest_keywords(
                    title=book.title,
                    keywords_type="broad",
                    keywords_count=5,
                    language=native_language,
                )
                _logger.info("Single keywords: %s", single_keywords)
                broad_research_single_campaign = BroadResearchSingleCampaign(book=book, text_keywords=single_keywords)
                broad_research_single_campaign.create()
                campaigns_created.append(broad_research_single_campaign.__class__.__name__)

            if CampaignPurpose.Exact_Scale in campaign_types:
                exact_scale_keywords: list[str] = TitleKeywordsSuggester.suggest_keywords(
                    title=book.title,
                    keywords_type="exact",
                    language=native_language,
                    length_inequality="at least",
                )
                _logger.info("Exact scale keywords: %s", exact_scale_keywords)
                exact_scale_campaign = ExactScaleCampaign(
                    book=book, text_keywords=exact_scale_keywords, default_bid=bid
                )
                exact_scale_campaign.create()
                campaigns_created.append(exact_scale_campaign.__class__.__name__)

            if CampaignPurpose.Exact_Scale_Single in campaign_types:
                exact_scale_single_keywords: list[str] = TitleKeywordsSuggester.suggest_keywords(
                    title=book.title,
                    keywords_type="exact",
                    keywords_count=5,
                    language=native_language,
                    length_inequality="at least",
                )
                _logger.info("Exact scale single keywords: %s", exact_scale_single_keywords)
                exact_scale_single_campaign = ExactScaleSingleCampaign(
                    book=book, text_keywords=exact_scale_single_keywords
                )
                exact_scale_single_campaign.create()
                campaigns_created.append(exact_scale_single_campaign.__class__.__name__)

            if CampaignPurpose.Product_Comp in campaign_types:
                _logger.info("Creating Product Comp campaign")
                keywords: list[str] = TitleKeywordsSuggester.suggest_keywords(
                    title=book.title, language=native_language
                )
                text_targets: list[str] = ASINFinder(book.profile.profile_server).search_similar_books_asins(
                    keywords, book
                )
                product_comp_campaign = ProductCompCampaign(book=book, text_targets=text_targets, default_bid=bid)
                product_comp_campaign.create()
                campaigns_created.append(product_comp_campaign.__class__.__name__)

            if CampaignPurpose.Product_Exp in campaign_types:
                _logger.info("Creating Product Exp campaign")
                keywords: list[str] = TitleKeywordsSuggester.suggest_keywords(
                    title=book.title, language=native_language
                )
                _logger.info("Product Exp suggested keywords: %s", keywords)
                text_targets: list[str] = ASINFinder(book.profile.profile_server).search_similar_books_asins(
                    keywords, book
                )
                product_comp_campaign = ProductExpCampaign(book=book, text_targets=text_targets, default_bid=bid)
                product_comp_campaign.create()
                campaigns_created.append(product_comp_campaign.__class__.__name__)

            if CampaignPurpose.Product_Own in campaign_types:
                if book.author:
                    _logger.info("Creating Product Own campaign")
                    asin_targets: list[str] = get_asins_for_product_own_campaign(book)
                    product_own_campaign = ProductOwnCampaign(book=book, text_targets=asin_targets, default_bid=DEFAULT_MAX_BID)
                    product_own_campaign.create()
                    campaigns_created.append(product_own_campaign.__class__.__name__)

            if CampaignPurpose.GP in campaign_types:
                _logger.info("Creating GP campaign")
                max_keyword_in_campaign = CAMPAIGN_MAX_TARGETS_MAP[CampaignPurpose.GP]
                keywords: list[str] = TitleKeywordsSuggester.suggest_keywords(
                    title=book.title, keywords_count=5, language=native_language
                )
                marketplace = getattr(Marketplaces, book.profile.country_code)
                book_format = "Kindle"
                classification_id = classificationIds[book.profile.country_code][book_format]
                keywords_to_create: Set[str] = set()
                for keyword in keywords:
                    asins = BookSearch(server_location=book.profile.profile_server).search_books(
                        keywords=[keyword],
                        classification_id=classification_id,
                        marketplace=marketplace,
                        max_results=100,
                    )
                    catalog_items = CatalogItems(
                        credentials=credentials[book.profile.profile_server],
                        marketplace=marketplace,
                    )
                    for asin in asins:
                        keywords_text = ""
                        book_details_response = catalog_items.get_catalog_item(
                            asin=asin,
                            includedData=["attributes"],
                            marketplaceIds=marketplace.marketplace_id,
                        )
                        time.sleep(1)
                        attributes = book_details_response.payload["attributes"]
                        title = attributes["item_name"][0]["value"]
                        if attributes.get("product_description"):
                            description = attributes.get("product_description")[0]["value"]
                        else:
                            description = ""
                        keywords_text += keywords_text + title + description
                        text_with_removed_specials = re.sub(r"[^\w\s]", "", keywords_text)
                        filtered_keywords = set(
                            [keyword.lower() for keyword in text_with_removed_specials.split() if len(keyword) > 4]
                        )
                        keywords_to_create = keywords_to_create.union(filtered_keywords)
                        if len(keywords_to_create) >= max_keyword_in_campaign:
                            keywords_to_create = set(list(keywords_to_create)[:max_keyword_in_campaign])

                gp_campaign = GPCampaign(book=book, text_keywords=list(keywords_to_create))
                gp_campaign.create()
                campaigns_created.append(gp_campaign.__class__.__name__)

            if CampaignPurpose.Auto_GP in campaign_types:
                auto_gp_campaign = AutoGPCampaign(book=book)
                auto_gp_campaign.create()
                campaigns_created.append(auto_gp_campaign.__class__.__name__)

            if CampaignPurpose.Discovery in campaign_types:
                discovery_campaign = DiscoveryCampaign(book=book, bid=bid)
                discovery_campaign.create()
                campaigns_created.append(discovery_campaign.__class__.__name__)

        except Exception as e:
            _logger.exception(e)
        finally:
            _logger.info("Campaigns created: %s for book with pk: %s", campaigns_created, book_pk)
