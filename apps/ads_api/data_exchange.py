import json
import logging
import math
import os
import random
import re
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import groupby
from statistics import StatisticsError, mean
from typing import Dict, List, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup
from django.db.models import Count, DecimalField, Exists, OuterRef, Q, QuerySet, Sum
from django.db.models import Value as V
from django.db.models.aggregates import Max
from django.db.models.functions import Coalesce
from django.utils import timezone
from requests.exceptions import RequestException

from adsdroid.celery import app, chain
from apps.ads_api.adapters.amazon_ads.sponsored_products.ad_group_adapter import (
    AdGroupAdapter,
)
from apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter import (
    CampaignAdapter,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.ad_group import AdGroupEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import (
    CampaignEntity,
    DynamicBidding,
    PlacementBidding,
)
from apps.ads_api.entities.amazon_ads.sponsored_products.keywords import KeywordEntity
from apps.ads_api.google_sheets import GoogleSheet, _process_read_values
from apps.ads_api.services.books.fill_with_negatives_services.fiil_with_negative_targets_service import (
    FillWithNegativeTargetsService,
)
from apps.ads_api.services.books.fill_with_negatives_services.fill_with_negative_keywords_service import (
    FillWithNegativeKeywordsService,
)

from ..sp_api import book_info
from ..utils.acronyms import generate_acronym
from ..utils.iso_to_epoch_converter import IsoToEpochConverter
from .adapters.amazon_ads.sponsored_products.campaign_negative_keywords_adapter import (
    CampaignNegativeKeywordsAdapter,
)
from .adapters.amazon_ads.sponsored_products.keywords_adapter import KeywordsAdapter
from .adapters.amazon_ads.sponsored_products.negative_keywords_adapter import (
    NegativeKeywordsAdapter,
)
from .adapters.amazon_ads.sponsored_products.negative_targets_adapter import (
    NegativeTargetsAdapter,
)
from .adapters.amazon_ads.sponsored_products.targets_adapter import TargetsAdapter
from .entities.amazon_ads.sponsored_products.negative_keyword import (
    NegativeKeywordEntity,
)
from .entities.amazon_ads.sponsored_products.negative_target import (
    Expression,
    NegativeTargetEntity,
)
from .entities.amazon_ads.sponsored_products.search_filters import (
    IdFilter,
    KeywordSearchFilter,
)
from .entities.amazon_ads.sponsored_products.targets import TargetEntity
from .exceptions.ads_api.base import BaseAmazonAdsException, ObjectNotCreatedError
from .repositories.book.price_repository import BookPriceRepository
from .repositories.campaign_repository import CampaignRepository
from .repositories.profile_repository import ProfileRepository
from .services.campaigns.build_campaign_entity_service import BuildCampaignEntityService
from .services.keywords.cleaner_service import KeywordsCleanerService
from .services.keywords.date_keywords_spends_service import DateKeywordsSpendsServce
from .services.profiles.proven_budget_service import ProvenBudgetService
from .services.profiles.remaining_daily_budget_service import (
    RemainingDailyBudgetService,
)
from .tasks import (
    campaign_clean_up,
    get_profile_book_catalog,
    sync_ad_groups,
    sync_campaigns,
    sync_product_ads,
    sync_profiles,
    update_books_details,
    update_profit_campaign_budgets,
)

path = os.getcwd()

from apps.ads_api.amazon_api import AdsAPI, get_new_retry_session
from apps.ads_api.campaigns.product.product_own_campaign import ProductOwnCampaign
from apps.ads_api.constants import *
from apps.ads_api.models import (
    AdGroup,
    Book,
    Campaign,
    CampaignPurpose,
    Keyword,
    NewRelease,
    ProductAd,
    Profile,
    Rank,
    RecentReportData,
    Relevance,
    Report,
    Target,
)

from ..utils.chunks import chunker

_logger = logging.getLogger(__name__)


def _get_managed_profiles(server: Optional[str] = None):
    """Gets all managed profiles for specified server or all servers"""
    # Only run for managed profiles
    managed_profiles = Profile.objects.filter(managed=True)
    # If the argument server was passed then only run for that server , further filter the managed profiles
    if server:
        managed_profiles = managed_profiles.filter(profile_server=server)
    return managed_profiles


@app.task
def sp_campaign_purpose_update(profile_ids: Optional[list[int]] = None):
    """Classify campaigns by campaign purpose by the types of keywords present"""
    # Method:
    # for each campaign which has a blank purpose, scan through the enabled keywords and classify based on types of keywords present
    # update the campaign model
    custom_filter = {"campaign_purpose": "", "sponsoring_type": "sponsoredProducts"}
    if profile_ids:
        profiles = Profile.objects.filter(id__in=profile_ids)
        custom_filter["profile__in"] = profiles  # type: ignore
    else:
        custom_filter["profile__managed"] = True  # type: ignore
    purposeless_campaigns = Campaign.objects.filter(**custom_filter).exclude(targeting_type="auto")
    if not purposeless_campaigns.exists():
        return
    for current_campaign in purposeless_campaigns:
        campaign_purpose = ""
        # Update campaign purpose from campaign name
        for purpose in CampaignPurpose:  # type: ignore
            if purpose == CampaignPurpose.GP:
                if (
                    f"-{purpose}-" in current_campaign.campaign_name
                    and "Auto" not in current_campaign.campaign_name
                ):
                    campaign_purpose = purpose
                    break
            else:
                if f"-{purpose}-" in current_campaign.campaign_name:
                    campaign_purpose = purpose
                    break
        if campaign_purpose == "":
            keyword_data, target_data = _get_campaign_targets(current_campaign)
            if keyword_data.exists():
                broad_phrase_keywords = keyword_data.filter(
                    Q(match_type=MatchType.BROAD.value) | Q(match_type=MatchType.PHRASE.value)
                )
                max_broad_phrase_bid = broad_phrase_keywords.aggregate(Max("bid"))["bid__max"]
                if max_broad_phrase_bid != None and max_broad_phrase_bid <= GP_MAX_BID:
                    campaign_purpose = CampaignPurpose.GP  # type: ignore
                elif broad_phrase_keywords.count() > 0:
                    if "-Single" in current_campaign.campaign_name:
                        campaign_purpose = CampaignPurpose.Broad_Research_Single  # type: ignore
                    else:
                        campaign_purpose = CampaignPurpose.Broad_Research  # type: ignore
                else:
                    exact_keywords = keyword_data.filter(match_type="exact")
                    if exact_keywords.count() > 0:
                        if "-Single" in current_campaign.campaign_name:
                            campaign_purpose = CampaignPurpose.Exact_Scale_Single  # type: ignore
                        else:
                            campaign_purpose = CampaignPurpose.Exact_Scale  # type: ignore
            elif target_data.exists():
                product_targets = target_data.filter(
                    resolved_expression_type=TargetingExpressionPredicateType.ASIN_SAME_AS.value
                )
                category_targets = target_data.filter(
                    resolved_expression_type=TargetingExpressionPredicateType.ASIN_CATEGORY_SAME_AS.value
                )
                if product_targets.count() > 0:
                    if "Auto-GP-" in current_campaign.campaign_name:
                        campaign_purpose = CampaignPurpose.Auto_GP  # type: ignore
                    elif "-Own" in current_campaign.campaign_name:
                        campaign_purpose = CampaignPurpose.Product_Own  # type: ignore
                    else:
                        campaign_purpose = CampaignPurpose.Product_Comp  # type: ignore
                elif category_targets.count() > 0:
                    campaign_purpose = CampaignPurpose.Cat_Research  # type: ignore
        if campaign_purpose == "":
            # logger.error(f"Campaign purpose for campaign {current_campaign.campaign_name} on profile {current_campaign.profile.nickname} [{current_campaign.profile.country_code}] still not clear. Review!")
            continue
        if campaign_purpose != "":
            current_campaign.campaign_purpose = campaign_purpose.value  # type: ignore
        # udpate Campaign model
    Campaign.objects.bulk_update(purposeless_campaigns, ["campaign_purpose"], batch_size=1000)


def _get_campaign_targets(current_campaign):
    """Gets a campaign's keywords and targets, enabled if available, all others if all paused or archived"""
    keyword_data = Keyword.objects.filter(
        campaign=current_campaign,
        state=SpState.ENABLED.value,
        keyword_type="Positive",
    )
    target_data = Target.objects.filter(
        campaign=current_campaign,
        state=SpState.ENABLED.value,
        keyword_type="Positive",
    )
    if keyword_data.count() > 0 or target_data.count() > 0:
        return keyword_data, target_data

    keyword_data = Keyword.objects.filter(
        campaign=current_campaign,
        keyword_type="Positive",
    )
    target_data = Target.objects.filter(
        campaign=current_campaign,
        keyword_type="Positive",
    )

    return keyword_data, target_data


@app.task
def get_asins_for_sp_campaigns(profile_ids: Optional[list[int]] = None):
    """Reads the Product Ads model to get ASIN(s) for active campaigns"""
    if not profile_ids:
        profile_ids = ProfileRepository.get_managed_profiles().values_list("id", flat=True)

    CampaignRepository.update_books_by_contained_product_ads_for_profiles(profile_ids)

def get_asins_for_product_own_campaign(book: Book):
    asins = Book.objects.filter(
        profile=book.profile,
        author=book.author,
        eligible=True
    ).values_list("asin", flat=True)
    return asins

def throwaway():
    """Throwaway function to test reloading of .py file with IPython shell"""
    var = "new function6"
    _logger.info("%s", var)


def print_td(t1, task_name: str):
    """Helper time tracking function"""
    # Time tracking code
    t2 = time.time()
    td = t2 - t1
    _logger.info("Run time for %s: %s.", task_name, td)


@app.task
def sync_keywords(
    endpoint: Optional[SpEndpoint] = None,
    server: Optional[ServerLocation] = None,
    profile_ids: Optional[list[int]] = None,
    managed_campaigns_only: Optional[bool] = True,
    campaign_id_amazon_list: Optional[list] = None,
):
    """Sync keywords data for managed profiles"""
    if profile_ids:
        profiles = Profile.objects.filter(id__in=profile_ids)
    else:
        # Only run for managed profiles
        profiles = Profile.objects.filter(managed=True)
    # If the argument server was passed then only run for that server , further filter the managed profiles
    if server:
        profiles = profiles.filter(profile_server=server)

    # Define default endpoints and their corresponding adapters
    default_endpoints = [
        (SpEndpoint.KEYWORDS, KeywordsAdapter),
        (SpEndpoint.NEGATIVE_KEYWORDS, NegativeKeywordsAdapter),
        (SpEndpoint.CAMPAIGN_NEGATIVE_KEYWORDS, CampaignNegativeKeywordsAdapter),
        (SpEndpoint.TARGETS, TargetsAdapter),
        (SpEndpoint.NEGATIVE_TARGETS, NegativeTargetsAdapter),
    ]

    # If endpoint is provided, use only that one with its corresponding adapter.
    # If endpoint is a tuple (endpoint, adapter), use as is.
    # If it's not a tuple, find its corresponding adapter in default_endpoints.
    if endpoint:
        if isinstance(endpoint, tuple):
            endpoints = [endpoint]
        else:
            endpoints = [e for e in default_endpoints if e[0] == endpoint]
    else:
        endpoints = default_endpoints

    for endpoint, Adapter in endpoints:
        model = _get_model_from_endpoint(endpoint)
        if not model:
            return
        for current_profile in profiles:
            adapter = Adapter(current_profile)
            campaigns = None
            if managed_campaigns_only:
                campaigns_int = list(
                    Campaign.objects.filter(
                        profile=current_profile,
                        managed=True,
                        sponsoring_type="sponsoredProducts",
                    )
                    .order_by("campaign_id_amazon")
                    .values_list("campaign_id_amazon", flat=True)
                    .distinct("campaign_id_amazon")
                )
                if len(campaigns_int) > 0:
                    _logger.info(f"{len(campaigns_int)} campaigns found for profile {current_profile}")
                    campaigns = list(map(str, campaigns_int))
                else:
                    _logger.info(f"No campaigns found for profile {current_profile}")
                    continue
            elif campaign_id_amazon_list:
                campaigns = campaign_id_amazon_list
            all_profile_keywords = []
            for campaign_batch_ids in chunker(campaigns, CAMPAIGNS_PER_TARGETS_REQUEST):
                profile_keywords_batch = adapter.list(
                    KeywordSearchFilter(
                        campaign_id_filter=IdFilter(include=campaign_batch_ids),
                    )
                )
                if profile_keywords_batch:
                    all_profile_keywords.extend(
                        [keyword.dict(exclude_none=True, by_alias=True) for keyword in profile_keywords_batch]
                    )
            _logger.info(
                f"{model.__name__}s returned from Amazon: {len(all_profile_keywords)} "
                f"for profile {current_profile}"
            )
            if not all_profile_keywords:
                continue
            profile_keywords_in_db_dict = _get_profile_keywords_dict(
                profile=current_profile, model=model, endpoint=endpoint
            )
            _logger.info(
                f"{model.__name__}s in db count: {len(profile_keywords_in_db_dict)}"
                f" for profile{current_profile}"
            )
            profile_campaigns_dict = _get_campaigns_for_profile_dict(current_profile)
            _logger.info(
                f"Campaigns in db count: {len(profile_keywords_in_db_dict)} " f"for profile {current_profile}"
            )
            if not profile_campaigns_dict:
                continue
            profile_ad_groups_dict = _get_ad_groups_for_profile_dict(current_profile)
            _logger.info(
                f"Ad groups in db count: {len(profile_keywords_in_db_dict)} " f"for profile {current_profile}"
            )

            if not profile_ad_groups_dict:
                continue
            keywords_to_update, keywords_to_create = _sort_keywords_create_update(
                all_profile_keywords,
                profile_keywords_in_db_dict,
                profile_campaigns_dict,
                profile_ad_groups_dict,
                model=model,
                endpoint=endpoint,
                profile=current_profile,
            )
            if len(keywords_to_create) > 0:
                _logger.info(
                    f"Keywords to create count: {len(keywords_to_create)} for profile {current_profile}"
                )
                model.objects.bulk_create(keywords_to_create, ignore_conflicts=True)
            if len(keywords_to_update) > 0:
                fields = _get_fields_to_update(endpoint=endpoint)
                _logger.info(
                    f"Keywords to update count: {len(keywords_to_update)} for profile {current_profile}"
                )
                model.objects.bulk_update(keywords_to_update, fields, batch_size=1000)

            objects_count = model.objects.filter(campaign__profile=current_profile).count()
            _logger.info(f"{current_profile} has {objects_count} in the end of sync [{model.__name__}]")


def _get_fields_to_update(endpoint: SpEndpoint):
    """Helper function to get model field to update"""
    fields = ["state", "serving_status", "last_updated_date_on_amazon"]
    if endpoint in [SpEndpoint.KEYWORDS, SpEndpoint.TARGETS]:
        fields.append("bid")
    return fields


def _get_model_from_endpoint(endpoint: SpEndpoint):
    """Helper function to match endpoint with Django model"""
    model = None
    if endpoint in [
        SpEndpoint.KEYWORDS,
        SpEndpoint.NEGATIVE_KEYWORDS,
        SpEndpoint.CAMPAIGN_NEGATIVE_KEYWORDS,
    ]:
        model = Keyword
    elif endpoint in [SpEndpoint.TARGETS, SpEndpoint.NEGATIVE_TARGETS]:
        model = Target
    elif endpoint == SpEndpoint.CAMPAIGNS:
        model = Campaign
    elif endpoint == SpEndpoint.AD_GROUPS:
        model = AdGroup
    elif endpoint == SpEndpoint.PRODUCT_ADS:
        model = ProductAd
    return model


def _sort_keywords_create_update(
    all_profile_keywords: list,
    profile_keywords_in_db_dict,
    profile_campaigns_dict,
    profile_ad_groups_dict,
    endpoint: SpEndpoint,
    model,
    profile: Profile,
):
    """
    Takes Amazon API response list of dictionaries of keywords, targets etc and
    cached DB dictionaries to create lists of keywords to update and create.
    """
    # set up some container variables
    missing_campaigns = set()
    keywords_to_update = []
    keywords_to_create = []
    current_keyword_in_db = None
    total_keywords_in_profile_db = len(profile_keywords_in_db_dict)
    identifier = "keywordId" if model._meta.model_name == "keyword" else "targetId"
    model_entry_identifier = "keyword_id" if model._meta.model_name == "keyword" else "target_id"
    for current_keyword in all_profile_keywords:
        if not current_keyword.get(identifier):
            continue
        keyword_id = int(current_keyword.get(identifier))
        if not current_keyword.get("campaignId"):
            continue
        keyword_campaign_id = int(current_keyword.get("campaignId"))
        keyword_ad_group_id = (
            int(current_keyword.get("adGroupId")) if current_keyword.get("adGroupId") else None
        )

        if keyword_campaign_id not in profile_campaigns_dict:
            missing_campaigns.add(keyword_campaign_id)
            continue

        defaults = _set_keyword_target_defaults(endpoint=endpoint, keyword_target_dict=current_keyword)
        campaign = profile_campaigns_dict[keyword_campaign_id]
        ad_group = profile_ad_groups_dict.get(keyword_ad_group_id)
        new_data = model(
            campaign=campaign,
            **defaults,
        )
        setattr(new_data, model_entry_identifier, keyword_id)
        if endpoint != SpEndpoint.CAMPAIGN_NEGATIVE_KEYWORDS:
            new_data.ad_group_id = int(current_keyword.get("adGroupId"))

        if total_keywords_in_profile_db != 0:
            current_keyword_in_db = profile_keywords_in_db_dict.get(keyword_id)
        if current_keyword_in_db:
            for amazon_field, db_field in VARIABLE_KEYWORD_FIELDS.items():
                value_db = getattr(current_keyword_in_db, db_field)
                value_amazon = current_keyword.get(amazon_field, 0)
                # "bid" will not be in keywords & targets which will use the ad group default bid
                if endpoint in [SpEndpoint.KEYWORDS, SpEndpoint.TARGETS] and amazon_field == "bid":
                    if "bid" not in current_keyword:
                        value_amazon = ad_group.default_bid if ad_group.default_bid else DEFAULT_BID
                        new_data.bid = value_amazon
                    if value_db is None:
                        value_db = 0
                    bid_difference = abs(float(value_amazon) - float(value_db))
                    if bid_difference < 0.011:
                        continue
                if value_amazon != value_db:
                    id = current_keyword_in_db.id
                    new_data.id = int(id)  # type:ignore
                    keywords_to_update.append(new_data)
                    break
        else:
            if endpoint in [SpEndpoint.KEYWORDS, SpEndpoint.TARGETS] and "bid" not in current_keyword:
                new_data.bid = ad_group.default_bid if ad_group.default_bid else DEFAULT_BID
            keywords_to_create.append(new_data)
        # temporary reporting functionality.
    if len(missing_campaigns) > 0:
        _logger.info(f"Profile: {profile} DB is missing campaigns with Amazon ids: {missing_campaigns}")
    return keywords_to_update, keywords_to_create


def _get_profile_data_from_API(profile, endpoint: SpEndpoint, campaigns: Optional[List] = None):
    """Get all keywords for a profile from Amazon API, using multiple requests to the API, if necessary"""
    data_count = MAX_KEYWORDS_API_RESPONSE
    start_index = 0
    all_profile_data = []
    while data_count == MAX_KEYWORDS_API_RESPONSE:
        params = {"startIndex": start_index}
        if campaigns:
            params["campaignIdFilter"] = ",".join(campaigns)  # type: ignore
        profile_keywords = AdsAPI.get_sp_data(
            server=profile.profile_server,
            profile_id=profile.profile_id,
            endpoint=endpoint,
            params=params,
        )
        if not profile_keywords:
            return None
        data_count = len(profile_keywords)
        start_index += MAX_KEYWORDS_API_RESPONSE
        all_profile_data.extend(profile_keywords)
    return all_profile_data


def _get_profile_keywords_dict(profile, model, endpoint: SpEndpoint):
    keyword_type = (
        "Negative"
        if endpoint
        in [
            SpEndpoint.NEGATIVE_KEYWORDS,
            SpEndpoint.CAMPAIGN_NEGATIVE_KEYWORDS,
            SpEndpoint.NEGATIVE_TARGETS,
        ]
        else "Positive"
    )
    profile_keywords_in_db = model.objects.filter(campaign__profile=profile, keyword_type=keyword_type)
    # additional filter to differentiate between negative keywords and campaign negatives which will have a blank Ad Group id
    if endpoint == SpEndpoint.CAMPAIGN_NEGATIVE_KEYWORDS:
        profile_keywords_in_db.filter(ad_group_id__isnull=True)
    # create a dictionary to hold all profile keywords to avoid hitting the db
    profile_keywords_in_db_dict = {}
    if profile_keywords_in_db.exists():
        bool(profile_keywords_in_db)
        column = "keyword_id" if model._meta.model_name == "keyword" else "target_id"
        for temp_keyword in profile_keywords_in_db:
            profile_keywords_in_db_dict[getattr(temp_keyword, column)] = temp_keyword
    return profile_keywords_in_db_dict


def _get_campaigns_for_profile_dict(current_profile):
    # create a dictionary to hold all profile campaigns to avoid hitting the db
    profile_campaigns = Campaign.objects.filter(profile=current_profile, sponsoring_type="sponsoredProducts")
    if not profile_campaigns.exists():
        return None
    profile_campaigns_dict = {}
    bool(profile_campaigns)
    for temp_campaign in profile_campaigns:
        profile_campaigns_dict[temp_campaign.campaign_id_amazon] = temp_campaign
    return profile_campaigns_dict


def _get_ad_groups_for_profile_dict(current_profile):
    # create a dictionary to hold all profile ad groups to avoid hitting the db
    profile_ad_groups = AdGroup.objects.filter(campaign__profile=current_profile)
    if not profile_ad_groups.exists():
        return None
    profile_ad_groups_dict = {}
    bool(profile_ad_groups)
    for temp_ad_group in profile_ad_groups:
        profile_ad_groups_dict[temp_ad_group.ad_group_id] = temp_ad_group
    return profile_ad_groups_dict


def _get_campaign_from_keyword_dict(campaign, current_keyword) -> Campaign:
    """Gets the campaign entry from the Campaign model table based on a keyword or target campaignId dictionary returned by Amazon API"""
    processing_campaign_id = current_keyword.get("campaignId")
    if hasattr(campaign, "campaign_id_amazon"):
        if campaign.campaign_id_amazon != processing_campaign_id:  # type: ignore
            campaign = Campaign.objects.get(campaign_id_amazon=processing_campaign_id)
    else:
        campaign = Campaign.objects.get(campaign_id_amazon=processing_campaign_id)
    return campaign


def _set_keyword_target_defaults(endpoint: SpEndpoint, keyword_target_dict: dict):
    """Helper function to set the defaults for Keyword and Target model population"""
    converter = IsoToEpochConverter()
    keyword_defaults = {
        "keyword_type": "Positive",
        "state": keyword_target_dict.get("state"),
        "serving_status": keyword_target_dict.get("extendedData").get("servingStatus"),  # type: ignore
        "last_updated_date_on_amazon": converter.iso_to_epoch(
            keyword_target_dict.get("extendedData").get("lastUpdateDateTime"),
            convert_to=TimeUnit.MILLISECOND,
        ),
    }

    if endpoint in [SpEndpoint.KEYWORDS, SpEndpoint.NEGATIVE_KEYWORDS]:
        keyword_defaults["keyword_text"] = keyword_target_dict.get("keywordText")
        keyword_defaults["match_type"] = keyword_target_dict.get("matchType")
    elif endpoint in [SpEndpoint.TARGETS, SpEndpoint.NEGATIVE_TARGETS]:
        keyword_defaults["resolved_expression_text"] = keyword_target_dict.get("resolvedExpression")[0].get(
            # type: ignore
            "value"
        )
        keyword_defaults["resolved_expression_type"] = keyword_target_dict.get("resolvedExpression")[0].get(
            # type: ignore
            "type"
        )  # type: ignore
    if endpoint == SpEndpoint.TARGETS:
        keyword_defaults["targeting_type"] = keyword_target_dict.get("expressionType")
    if endpoint in [SpEndpoint.KEYWORDS, SpEndpoint.TARGETS]:
        keyword_defaults["bid"] = keyword_target_dict.get("bid")
    elif endpoint in [
        SpEndpoint.NEGATIVE_KEYWORDS,
        SpEndpoint.NEGATIVE_TARGETS,
        SpEndpoint.CAMPAIGN_NEGATIVE_KEYWORDS,
    ]:
        keyword_defaults["keyword_type"] = "Negative"

    return keyword_defaults


@dataclass
class AdSlice:
    """Data class used to represent a performance slice of a keyword or campaign placement"""

    sales: float = 0.0
    spend: float = 0.0
    kenp_royalties: int = 0
    impressions: int = 0
    clicks: int = 0
    orders: int = 0
    attributed_conversions_30d: int = 0

    def add(self, new_data):
        self.sales = self.sales + float(new_data.sales)
        self.spend = self.spend + float(new_data.spend)
        self.kenp_royalties = self.kenp_royalties + new_data.kenp_royalties
        self.impressions = self.impressions + new_data.impressions
        self.clicks = self.clicks + new_data.clicks
        self.orders = self.orders + new_data.orders


def _calculate_bid_good_sellers(slice_list, target_acos):
    """Helper function to calculate bid of targets which are selling well"""
    sales_peg = 0.0
    bid_to_return = 0.0
    target_acos = float(target_acos)
    for chunk in chunker(slice_list, PROFITABLE_TARGET_CHUNK_DAYS):
        chunk_totals = _add_up_ad_slice(slice_list=chunk)
        if chunk_totals.sales > 0 and chunk_totals.clicks > 0 and chunk_totals.orders > 2:
            acos = chunk_totals.spend / chunk_totals.sales
            if acos < target_acos * RESEARCH_MARGIN_MULTIPLIER and chunk_totals.sales > sales_peg:
                sales_peg = chunk_totals.sales
                cpc = round(chunk_totals.spend / chunk_totals.clicks, 2)
                if acos < 0.75 * target_acos:
                    bid_to_return = cpc / 0.75
                elif acos < target_acos:
                    bid_to_return = cpc / (acos / target_acos)
                else:
                    bid_to_return = cpc
    if bid_to_return == 0.0:
        # set the ideal bid using the whole data set
        slice_totals = _add_up_ad_slice(slice_list=slice_list)
        bid_to_return = (
            slice_totals.kenp_royalties + (slice_totals.sales * target_acos)
        ) / slice_totals.clicks
    return round(bid_to_return, 2)


def log_bids_changes(
    profile: Profile,
    bid_changes,
):
    proven_bid_changing_trends = defaultdict(list)
    unproven_bid_changing_trends = defaultdict(list)
    for keyword in bid_changes:
        choosed_keyword_type = (
            proven_bid_changing_trends if keyword["is_proven"] else unproven_bid_changing_trends
        )
        if keyword["bid_change"] < 0:
            choosed_keyword_type["dicreased"].append(keyword["bid_change"])
        elif keyword["bid_change"] > 0:
            choosed_keyword_type["increased"].append(keyword["bid_change"])
        else:
            choosed_keyword_type["without_changes"].append(keyword["bid_change"])

    try:
        proven_dicreased_mean = round(mean(proven_bid_changing_trends["dicreased"]), 3)
    except StatisticsError:
        proven_dicreased_mean = 0
    proven_dicreased_count = len(proven_bid_changing_trends["dicreased"])
    try:
        proven_increased_mean = round(mean(proven_bid_changing_trends["increased"]), 3)
    except StatisticsError:
        proven_increased_mean = 0
    proven_increased_count = len(proven_bid_changing_trends["increased"])
    proven_without_changes = len(proven_bid_changing_trends["without_changes"])

    try:
        unproven_dicreased_mean = round(mean(unproven_bid_changing_trends["dicreased"]), 3)
    except StatisticsError:
        unproven_dicreased_mean = 0
    unproven_dicreased_count = len(unproven_bid_changing_trends["dicreased"])
    try:
        unproven_increased_mean = round(mean(unproven_bid_changing_trends["increased"]), 3)
    except StatisticsError:
        unproven_increased_mean = 0
    unproven_increased_count = len(unproven_bid_changing_trends["increased"])
    unproven_without_changes = len(unproven_bid_changing_trends["without_changes"])

    _logger.info(
        "[%s] Unproven bids increased count: %s, increased mean: %s",
        profile,
        unproven_increased_count,
        unproven_increased_mean,
    )
    _logger.info(
        "[%s] Unproven bids dicreased count: %s, dicreased mean: %s",
        profile,
        unproven_dicreased_count,
        unproven_dicreased_mean,
    )
    _logger.info(
        "[%s] Count of unproven bids without changing: %s",
        profile,
        unproven_without_changes,
    )

    _logger.info(
        "[%s] Proven bids increased count: %s, increased mean: %s",
        profile,
        proven_increased_count,
        proven_increased_mean,
    )
    _logger.info(
        "[%s] Proven bids dicreased count: %s, dicreased mean: %s",
        profile,
        proven_dicreased_count,
        proven_dicreased_mean,
    )
    _logger.info(
        "[%s] Count of proven bids without changing: %s",
        profile,
        proven_without_changes,
    )


@app.task
def update_sp_bids_status(
    profile_pks: list[int],
):
    """Update bids and status for managed campaigns of managed profiles"""
    # TODO: add never negatives list
    GP_PURPOSES = [CampaignPurpose.GP, CampaignPurpose.Auto_GP]

    if profile_pks:
        managed_profiles = Profile.objects.filter(id__in=profile_pks)
    else:
        managed_profiles = Profile.objects.filter(managed=True)

    if not managed_profiles.exists():
        return
    # Consider keywords fromt he last 30 days, excluding the last two days.
    date_from = datetime.today() - timedelta(days=MAX_DATA_TIMEFRAME_DAYS)
    # date_to = today - timedelta(days=DEFAULT_DATA_ACCURACY_CUTOFF_DAYS)
    mod_limit_date = datetime.today() - timedelta(days=0.8)
    # get the epoch time of 24 hours ago to ensure bid changes are not made too often
    mod_limit_epoch_ms = mod_limit_date.timestamp() * 1000
    # temporary ACOS settings and other inputs

    all_books = Book.objects.filter(profile__in=managed_profiles).order_by("profile_id")
    books_per_profile_id = {
        profile_id: list(books) for profile_id, books in groupby(all_books, key=lambda book: book.profile_id)
    }

    for profile in managed_profiles:
        keywords = {}
        report_data_per_keyword = {}
        be_acos_per_book = {
            book.asin: BookData(
                asin=book.asin,
                price=float(book.price),
                be_acos=float(book.be_acos),
                reviews=book.reviews,
            )
            for book in books_per_profile_id.get(profile.id, [])
        }
        if not be_acos_per_book:
            continue

        for model, report_type, identifier in [
            (Keyword, SpReportType.KEYWORD, "keyword_id"),
            (Target, SpReportType.TARGET, "target_id"),
        ]:
            # Get all keywords where campaign is managed, keyword is serving and hasn't been updated in the last 24 hrs
            keywords[identifier]: [Union[QuerySet[Keyword], QuerySet[Target]]] = (
                model.objects.prefetch_related("campaign__books")
                .select_related("campaign")
                .filter(
                    campaign__profile=profile,
                    campaign__managed=True,
                    serving_status__in=TARGETS_VALID_STATUSES,
                    last_updated_date_on_amazon__lt=mod_limit_epoch_ms,
                    keyword_type="Positive",
                )
                .exclude(
                    Q(campaign__campaign_purpose__in=GP_PURPOSES)
                    | Q(campaign__campaign_name__regex=r"(-|_)GP(-|_)|Auto-GP(-|$)"),
                )
                .exclude(
                    campaign__books__asin__isnull=True,
                    bid__isnull=True,
                )
                .values(
                    identifier,
                    "campaign__profile_id",
                    "bid",
                    "campaign__target_acos",
                    "campaign__books__asin",
                    "campaign__books__pk",
                )
                .order_by("campaign__profile_id")
            )

            report_data_per_keyword[identifier] = (
                RecentReportData.objects.select_related("campaign")
                .filter(
                    report_type=report_type,
                    campaign__profile=profile,
                    campaign__managed=True,
                    date__gte=date_from,
                    **{f"{identifier}__in": keywords[identifier].values(identifier)},
                )
                .exclude(
                    Q(campaign__campaign_purpose__in=GP_PURPOSES)
                    | Q(campaign__campaign_name__regex=r"(-|_)GP(-|_)|Auto-GP(-|$)")
                )
                .values(identifier)
                .annotate(sales_sum=Sum("sales"))
                .annotate(spend_sum=Sum("spend"))
                .annotate(kenp_royalties_sum=Sum("kenp_royalties"))
                .annotate(impressions_sum=Sum("impressions"))
                .annotate(clicks_sum=Sum("clicks"))
                .annotate(orders_sum=Sum("orders"))
                .annotate(attributed_conversions_30d_sum=Sum("attributed_conversions_30d"))
                .annotate(
                    book_launch=Exists(Book.objects.filter(campaigns=OuterRef("campaign"), launch=True))
                )
                .order_by("-sales_sum", "-book_launch", "spend_sum")
            )

            # excluding December 5th to 25th if we are in Q1
            if 1 <= datetime.today().month <= 3:
                excluded_year = datetime.today().year - 1
                exclude_date_from = datetime(excluded_year, 12, 5)
                exclude_date_to = datetime(excluded_year, 12, 25)

                report_data_per_keyword[identifier] = report_data_per_keyword[identifier].exclude(
                    date__range=[exclude_date_from, exclude_date_to]
                )

        bid_change_and_pause_per_keyword = get_bid_change_and_pause_per_keyword(
            be_acos_per_book,
            profile,
            report_data_per_keyword,
            keywords,
        )
        _logger.info("[%s] %s", profile, f"{model.__name__}s")

        for identifier, keywords_data in bid_change_and_pause_per_keyword.items():
            Entity = KeywordEntity if identifier == "keywordId" else TargetEntity
            keywords_to_update = []
            log_bids_changes(profile=profile, bid_changes=keywords_data)

            for keyword in keywords_data:
                bid_change = keyword["bid_change"]
                pause = keyword["pause"]
                if bid_change != 0 or pause is True:
                    kw_updates = {"external_id": keyword["external_id"]}
                    if pause:
                        kw_updates["state"] = SpState.PAUSED
                    elif bid_change != 0:
                        current_bid = keyword["current_bid"]
                        bid = round(float(current_bid) + bid_change, 2)
                        bid_str = str(bid)
                        if len(bid_str[bid_str.index(".") + 1 :]):
                            bid += 0.01

                        if bid < DEFAULT_MIN_BID:
                            bid = DEFAULT_MIN_BID
                        elif bid > DEFAULT_MAX_BID:
                            bid = DEFAULT_MAX_BID

                        kw_updates["bid"] = bid
                    keywords_to_update.append(
                        Entity.parse_obj(kw_updates).dict(exclude_none=True, by_alias=True)
                    )

            kw_count = len(keywords_to_update)

            Adapter = KeywordsAdapter if identifier == "keywordId" else TargetsAdapter
            adapter = Adapter(profile)
            adapter.batch_update(keywords_to_update)

            _logger.info(
                "Keywords updated: %s. Profile %s [%s]",
                kw_count,
                profile,
                profile.country_code,
            )
        # print(f"Targets updated: {kw_count}. Profile: {current_profile.nickname} [{current_profile.country_code}]")


def get_bid_change_and_pause_per_keyword(
    be_acos_per_book,
    profile,
    report_data_per_keyword,
    managed_keywords,
):
    # create a dictionary with all the keyword / target data aggregated for all managed keywords
    profile_id = profile.profile_id
    date_of_spend = datetime.today() - timedelta(days=1)
    bid_change_and_pause_per_keyword = {}

    proven_keywords_ids = {identifier: [] for identifier in managed_keywords.keys()}
    for identifier, reports_data in report_data_per_keyword.items():
        identifier_amazon = "keywordId" if identifier == "keyword_id" else "targetId"
        bid_change_and_pause_per_keyword[identifier_amazon] = []
        for report_data in reports_data:
            keyword = (
                managed_keywords[identifier].filter(**{f"{identifier}": report_data[identifier]}).first()
            )
            keyword_id = keyword[identifier]
            current_bid = keyword.get("bid")
            target_acos = keyword.get("campaign__target_acos")
            asin = keyword["campaign__books__asin"]
            book_id = keyword["campaign__books__pk"]

            if target_acos == 0:
                target_acos = be_acos_per_book[asin].be_acos if asin in be_acos_per_book else DEFAULT_BE_ACOS

            try:
                book_price_repo = BookPriceRepository(book_id)
                book_price = book_price_repo.get_actual_price()
            except (TypeError, AttributeError):
                book_price = DEFAULT_BOOK_PRICE

            book_reviews = be_acos_per_book[asin].reviews if asin else 0

            bid_change, pause = _campaign_adjust_keywords(
                report_data=report_data,
                target_acos=target_acos,
                current_val=current_bid,
                book_price=book_price,
                book_reviews=book_reviews,
            )
            if report_data["sales_sum"] > 0:
                proven_keywords_ids[identifier].append(keyword_id)

            bid_change_and_pause_per_keyword[identifier_amazon].append(
                {
                    "external_id": keyword_id,
                    "current_bid": current_bid,
                    "bid_change": bid_change,
                    "pause": pause,
                    "is_proven": bool(report_data["sales_sum"] > 0),
                }
            )

    outstanding_daily_budget_service = RemainingDailyBudgetService(profile_id)
    outstanding_daily_budget = outstanding_daily_budget_service.calculate()
    _logger.info(
        "Outstanding daily budget for profile %s equals %s",
        profile,
        outstanding_daily_budget,
    )

    proven_budget_service = ProvenBudgetService(profile)
    proven_budget = proven_budget_service.calculate()
    unproven_budget = outstanding_daily_budget - proven_budget
    _logger.info(
        "Budget for profile %s equals proven=%s unproven=%s",
        profile,
        proven_budget,
        unproven_budget,
    )

    proven_spend = 0
    unproven_spend = 0
    proven_keywords_count = 0
    unproven_keywords_count = 0
    for identifier, keywords in managed_keywords.items():
        # adopte for target
        proven_keywords = keywords.filter(**{f"{identifier}__in": proven_keywords_ids[identifier]})
        unproven_keywords = keywords.exclude(**{f"{identifier}__in": proven_keywords_ids[identifier]})
        proven_keywords_count += proven_keywords.count()
        unproven_keywords_count += unproven_keywords.count()
        proven_spends_service = DateKeywordsSpendsServce(date_of_spend, proven_keywords)
        proven_spend += proven_spends_service.calculate_spends()
        unproven_spends_service = DateKeywordsSpendsServce(date_of_spend, unproven_keywords)
        unproven_spend += unproven_spends_service.calculate_spends()

    total_spend = proven_spend + unproven_spend
    _logger.info(
        "Spend for date %s for profile %s equals proven=%s, unproven=%s",
        date_of_spend,
        profile,
        proven_spend,
        unproven_spend,
    )

    overspend = total_spend > outstanding_daily_budget
    # assume 10% overspend or 10% underspend
    predicted_modifier = 0.9 if overspend else 1.1

    predicted_proven_spend = float(proven_spend) * predicted_modifier
    predicted_unproven_spend = float(unproven_spend) * predicted_modifier
    _logger.info(
        "Predicted spend for profile %s equals proven=%s, unproven=%s",
        profile,
        predicted_proven_spend,
        predicted_unproven_spend,
    )

    surplus_budget = outstanding_daily_budget - predicted_proven_spend - predicted_unproven_spend

    _logger.info("Surples budget for profile %s equals %s", profile, surplus_budget)
    if surplus_budget < 0:
        proven_percentage_to_min = (
            (1 - proven_budget / predicted_proven_spend) if predicted_proven_spend > 0 else 0
        )
        proven_count_to_min = round(proven_keywords_count * proven_percentage_to_min)

        unproven_percentage_to_min = (
            (1 - unproven_budget / predicted_unproven_spend) if predicted_unproven_spend > 0 else 0
        )

        unproven_count_to_min = round(unproven_keywords_count * unproven_percentage_to_min)

        _logger.info(
            "proven_percentage_to_min=%s, proven_count_to_min=%s,"
            " unproven_percentage_to_min=%s, unproven_count_to_min=%s",
            proven_percentage_to_min,
            proven_count_to_min,
            unproven_percentage_to_min,
            unproven_count_to_min,
        )

        proven_keywords_to_min = []
        for identifier, _ in managed_keywords.items():
            proven_keywords_to_min += report_data_per_keyword[identifier].filter(sales_sum__gt=0)

        proven_keywords_to_min.sort(key=lambda k: (k["sales_sum"], -k["spend_sum"], k["book_launch"]))

        for report_data in proven_keywords_to_min[:proven_count_to_min]:
            identifier = "keyword_id" if "keyword_id" in report_data.keys() else "target_id"
            identifier_amazon = "keywordId" if identifier == "keyword_id" else "targetId"

            keyword = (
                managed_keywords[identifier].filter(**{f"{identifier}": report_data[identifier]}).first()
            )
            current_bid = float(keyword["bid"])

            keyword_data = list(
                filter(
                    lambda k: k["external_id"] == report_data[identifier],
                    bid_change_and_pause_per_keyword[identifier_amazon],
                )
            )[0]
            keyword_data["bid_change"] = DEFAULT_MIN_BID - current_bid

        unproven_keywords_to_min = []
        for identifier, _ in managed_keywords.items():
            unproven_keywords_to_min += report_data_per_keyword[identifier].filter(sales_sum=0)

        unproven_keywords_to_min.sort(key=lambda k: (-k["book_launch"], -k["spend_sum"]))

        for report_data in unproven_keywords_to_min[:unproven_count_to_min]:
            identifier = "keyword_id" if "keyword_id" in report_data.keys() else "target_id"
            identifier_amazon = "keywordId" if identifier == "keyword_id" else "targetId"

            keyword = (
                managed_keywords[identifier].filter(**{f"{identifier}": report_data[identifier]}).first()
            )
            current_bid = float(keyword["bid"])

            keyword_data = list(
                filter(
                    lambda k: k["external_id"] == report_data[identifier],
                    bid_change_and_pause_per_keyword[identifier_amazon],
                )
            )[0]
            keyword_data["bid_change"] = DEFAULT_MIN_BID - current_bid

        surplus_budget = 0

    profile.surplus_budget = surplus_budget
    profile.save()

    return bid_change_and_pause_per_keyword


def _adjust_bid_by_placement(placement_data_single, current_keyword, bid):
    """Adjusts the bid by the placement multiplier"""
    campaign_pk = current_keyword.campaign.pk
    placement_mult = placement_data_single[campaign_pk] if campaign_pk in placement_data_single else 0.0
    placement_mult = 1 + placement_mult / 100
    adjusted_bid = round(float(bid) / placement_mult, 2)
    bid_str = str(adjusted_bid)
    if len(bid_str[bid_str.index(".") + 1 :]):
        adjusted_bid += 0.01
    return adjusted_bid


def _calculate_combined_placement(current_profile: Profile, date_from: datetime, placement_mults: Dict):
    """Calculated the combined placement multiplier for bid set adjustment"""
    placement_data = (
        RecentReportData.objects.filter(
            report_type=SpReportType.PLACEMENT,
            campaign__profile=current_profile,
            campaign__managed=True,
            date__gte=date_from,
            # date__lte=date_to,
        )
        .exclude(campaign__campaign_name__contains="-GP-")
        .exclude(campaign__campaign_name__contains="_GP_")
        .exclude(campaign__campaign_purpose="GP")
    ).order_by("-date")
    if not placement_data.exists():
        return {}
    # create a dictionary with all the placement data aggregated for all managed campaigns
    placement_data_mem_list: Dict[int, List[AdSlice]] = {}
    for datum in placement_data:
        if datum.placement == "Top of Search on-Amazon":
            placement = "tos"
        elif datum.placement == "Detail Page on-Amazon":
            placement = "pp"
        else:
            # skip other placements
            continue
        campaign_pk = str(datum.campaign.pk)
        placement_data_mem_list = _collect_report_datums(
            datum=datum,
            datum_id=campaign_pk + "_" + placement,
            data_mem=placement_data_mem_list,
        )

    # total up the list of ad slices and store in dictionary
    placement_data_mem: Dict[int, Dict[str, AdSlice]] = {}
    for ident, slice_list in placement_data_mem_list.items():
        pos = ident.find("_")  # type: ignore
        pk = int(ident[:pos])  # type: ignore
        placement = ident[pos + 1 :]  # type: ignore
        placement_data_mem[pk] = {}
        placement_data_mem[pk][placement] = _add_up_ad_slice(slice_list=slice_list)

    placement_data_single = {}
    for ident, placement_dicts in placement_data_mem.items():
        slice_pp = placement_dicts["pp"] if "pp" in placement_dicts else AdSlice(0.0, 0.0, 0, 0, 0, 0)
        slice_tos = placement_dicts["tos"] if "tos" in placement_dicts else AdSlice(0.0, 0.0, 0, 0, 0, 0)
        mult_pp = placement_mults[ident]["pp"] if "pp" in placement_mults[ident] else 0.0
        mult_tos = placement_mults[ident]["tos"] if "tos" in placement_mults[ident] else 0.0
        balance_percent = (
            slice_tos.sales / (slice_tos.sales + slice_pp.sales)
            if slice_tos.sales + slice_pp.sales > 0
            else 0.0
        )
        # combined placement shows the placement to use for bids value offset
        combined_placement = (mult_tos - mult_pp) * balance_percent + mult_pp
        placement_data_single[ident] = combined_placement

    return placement_data_single


def _campaign_adjust_keywords(
    report_data: dict,
    current_val,
    target_acos=DEFAULT_BE_ACOS,
    book_price=DEFAULT_BOOK_PRICE,
    book_reviews: Optional[int] = None,
):
    """Bid and placement multiplier adjustment decision tree"""
    val_change = 0.0
    pause = False
    spend = float(report_data["spend_sum"])
    clicks = float(report_data["clicks_sum"])
    if spend == 0:
        cpc = 0.0
    elif clicks < 1:
        cpc = DEFAULT_CPC
    else:
        cpc = round(spend / clicks, 2)
    pause_threshold = book_price if book_price < PAUSE_TRESHOLD else PAUSE_TRESHOLD
    default_max_bid = DEFAULT_MAX_BID
    target_acos = float(target_acos)
    default_min_bid = DEFAULT_MIN_BID if spend < (book_price * target_acos) else DEFAULT_MAX_BID_CONSERVATIVE

    if book_price == 0:
        book_price = DEFAULT_BOOK_PRICE
    if book_reviews is not None and book_reviews < MIN_BOOK_REVIEWS:
        default_max_bid = DEFAULT_MAX_BID_CONSERVATIVE
        default_min_bid = DEFAULT_MIN_BID
    # allow for kenp royalties by offsetting the spend
    if report_data["kenp_royalties_sum"] > spend:
        spend = 0.01  # this will result in a positive & very low ACOS => increase in bid
    elif report_data["kenp_royalties_sum"] > 0:
        spend = spend - report_data["kenp_royalties_sum"]
    # main multiplier change decision tree starts
    # 2 different decision trees are used for with and without sales
    # keyword_sales = 0 so check on profile mode then research if allowed
    if report_data["sales_sum"] == 0:
        if spend > pause_threshold:
            pause = True
        # if there are no spend, then do more research
        elif spend == 0:
            if report_data["impressions_sum"] >= IMP_TRESHOLD and current_val > default_min_bid:
                val_change = -1 * SML_BID_CHANGE
            elif (
                report_data["impressions_sum"] < IMP_TRESHOLD
                and default_min_bid < current_val < default_max_bid
            ):
                val_change = SML_BID_CHANGE
        # if there is spend then decide on how much more research to do
        else:
            # look at the research spend threshold which is obtained from the book price and target ACOS
            research_spend_threshold = round(target_acos * float(book_price) * RESEARCH_MARGIN_MULTIPLIER, 2)
            # if bid can be decreased and spend > 1.25 x 40% x 10
            if spend >= research_spend_threshold and current_val > default_min_bid:
                phantom_acos = round(spend / float(book_price), 2)
                # work around to align with functionality of the other code, using val change, not the full bid.
                bid_to_return = round(cpc / (phantom_acos / target_acos), 2) if cpc > 0 else 0.0
                val_change = round(bid_to_return - float(current_val), 2)
                if val_change >= 0:
                    val_change = -2 * BIG_BID_CHANGE
                # if it's going to be lower than Min Bid, just set Min Bid
                if float(current_val) + val_change < default_min_bid:
                    val_change = round(default_min_bid - float(current_val), 2)
            # do more research
            if (
                spend < research_spend_threshold
                and current_val < BID_UPPER_THRESHOLD * cpc
                and current_val < default_max_bid
            ):
                # next click could possibly get a good ACOS sale
                val_change = SML_BID_CHANGE
    else:  # there are sales, use a formula to work out the new bid based on the CPC
        acos = spend / float(report_data["sales_sum"])
        if acos == 0:
            _logger.error(f'ACOS is zero error, spend was: {spend}, sales was: {report_data["sales_sum"]}')
            return 0.0, False
        acos_ratio = acos / target_acos
        bid_cpc_multiplier = -0.1219 * acos_ratio**2 - 0.3564 * acos_ratio + 1.703
        bid_to_return = round(bid_cpc_multiplier * cpc, 2)
        bid_to_return = min(
            max(bid_to_return, DEFAULT_MIN_BID), default_max_bid
        )  # Using the ALL CAPS DEFAULT_MIN_BID is correct
        val_change = round(bid_to_return - float(current_val), 2)

    return val_change, pause


def _campaign_adjust(
    slice: AdSlice,
    current_val,
    target_acos=DEFAULT_BE_ACOS,
    book_price=DEFAULT_BOOK_PRICE,
    book_reviews: Optional[int] = None,
):
    """Bid and placement multiplier adjustment decision tree"""
    val_change = 0.0
    pause = False

    if slice.spend == 0:
        cpc = 0.0
    elif slice.clicks < 1:
        cpc = DEFAULT_CPC
    else:
        cpc = round(float(slice.spend) / float(slice.clicks), 2)
    pause_threshold = book_price if book_price < PAUSE_TRESHOLD else PAUSE_TRESHOLD
    default_max_bid = DEFAULT_MAX_BID
    default_min_bid = (
        DEFAULT_MIN_BID if slice.spend < (book_price * target_acos) else DEFAULT_MAX_BID_CONSERVATIVE
    )
    target_acos = float(target_acos)

    if book_price == 0:
        book_price = DEFAULT_BOOK_PRICE
    if book_reviews is not None and book_reviews < MIN_BOOK_REVIEWS:
        default_max_bid = DEFAULT_MAX_BID_CONSERVATIVE
        default_min_bid = DEFAULT_MIN_BID
    # allow for kenp royalties by offsetting the spend
    if slice.kenp_royalties > slice.spend:
        slice.spend = 0.01  # this will result in a positive & very low ACOS => increase in bid
    elif slice.kenp_royalties > 0:
        slice.spend = slice.spend - slice.kenp_royalties
    # main multiplier change decision tree starts
    # 2 different decision trees are used for with and without sales
    # keyword_sales = 0 so check on profile mode then research if allowed
    if slice.sales == 0:
        if slice.spend > pause_threshold:
            pause = True
        # if there are no clicks, then do more research
        elif slice.clicks == 0:
            if slice.impressions >= IMP_TRESHOLD and current_val > default_min_bid:
                val_change = -1 * SML_BID_CHANGE
            elif slice.impressions < IMP_TRESHOLD and default_min_bid < current_val < default_max_bid:
                val_change = SML_BID_CHANGE
        # if there are clicks then decide on how much more research to do
        else:
            # look at the research spend threshold which is obtained from the book price and target ACOS
            research_spend_threshold = round(target_acos * float(book_price) * RESEARCH_MARGIN_MULTIPLIER, 2)
            # if bid can be decreased and spend > 1.25 x 40% x 10
            if slice.spend >= research_spend_threshold and current_val > default_min_bid:
                phantom_acos = round(float(slice.spend) / float(book_price), 2)
                # work around to align with functionality of the other code, using val change, not the full bid.
                bid_to_return = round(cpc / (phantom_acos / target_acos), 2) if cpc > 0 else 0.0
                val_change = round(bid_to_return - float(current_val), 2)
                if val_change >= 0:
                    val_change = -2 * BIG_BID_CHANGE
                # if it's going to be lower than Min Bid, just set Min Bid
                if float(current_val) + val_change < default_min_bid:
                    val_change = round(default_min_bid - float(current_val), 2)
            # do more research
            if (
                slice.spend < research_spend_threshold
                and current_val < BID_UPPER_THRESHOLD * cpc
                and current_val < default_max_bid
            ):
                # next click could possibly get a good ACOS sale
                val_change = SML_BID_CHANGE
    else:  # there are sales, use a formula to work out the new bid based on the CPC
        acos = float(slice.spend) / float(slice.sales)
        if acos == 0:
            _logger.error(
                f"ACOS is zero error, spend was: {float(slice.spend)}, sales was: {float(slice.sales)}"
            )
            return 0.0, False
        acos_ratio = acos / target_acos
        bid_cpc_multiplier = -0.1219 * acos_ratio**2 - 0.3564 * acos_ratio + 1.703
        bid_to_return = round(bid_cpc_multiplier * cpc, 2)
        bid_to_return = min(
            max(bid_to_return, DEFAULT_MIN_BID), default_max_bid
        )  # Using DEFAULT_MIN_BID is correct here
        val_change = round(bid_to_return - float(current_val), 2)
    return val_change, pause


###############################################################################################################
###############################################################################################################
###############################################################################################################


# get a Dict[target_id, List[AdSlice()]]
# for each Dict, get total orders
# if orders >= 5: find best chunk, and set bid:
#   if be_acos <= ACOS < 1.25*be_acos then set bid to CPC
#   elif: 0.5*be_acos <= ACOS < be_acos then CPC / mult (where mult would be 0.5 - 1.0)
#   elif: ACOS < 0.5*be_acos then CPC / mult (where mult would be 0.5)
# else: set the ideal bid * Mult


def _collect_report_datums(datum, datum_id, data_mem: Dict[int, List[AdSlice]]):
    """Helper function to collect lists of AdSlices for report data for keywords, targets, placements"""
    if datum_id in data_mem:
        data_mem[datum_id].append(datum)
    else:
        data_mem[datum_id] = [datum]
    return data_mem


def _add_up_ad_slice(slice_list: List[RecentReportData]) -> AdSlice:
    slice_totals = AdSlice(
        sales=0.0,
        spend=0.0,
        kenp_royalties=0,
        impressions=0,
        clicks=0,
        orders=0,
    )
    for slice in slice_list:
        slice_totals.spend += float(slice.spend)
        slice_totals.kenp_royalties += slice.kenp_royalties
        slice_totals.impressions += slice.impressions
        slice_totals.clicks += slice.clicks
        slice_totals.orders += slice.orders
        slice_totals.sales += float(slice.sales)

    return slice_totals


###############################################################################################################
###############################################################################################################
###############################################################################################################


@app.task
def udpate_sp_placements(profile_pks: list[int]):
    """Update placements for managed profiles"""
    # Only run for managed profiles
    if profile_pks:
        managed_profiles = Profile.objects.filter(id__in=profile_pks).prefetch_related("book_set")
    else:
        managed_profiles = Profile.objects.filter(managed=True).prefetch_related("book_set")

    # Consider keywords fromt he last 30 days, excluding the last two days.
    today = datetime.today()
    date_min_data = datetime.date(today - timedelta(days=7))
    # date_from = today - timedelta(days=DEFAULT_DATA_TIMEFRAME_DAYS)
    # date_to = today - timedelta(days=DEFAULT_DATA_ACCURACY_CUTOFF_DAYS)
    mod_limit_date = today - timedelta(days=0.8)
    # get the epoch time of 24 hours ago to ensure bid changes are not made too often
    mod_limit_epoch_ms = mod_limit_date.timestamp() * 1000
    # temporary ACOS settings and other inputs
    for current_profile in managed_profiles:
        profile_id = current_profile.profile_id
        profile_server = current_profile.profile_server

        be_acos_per_book = {
            book.asin: BookData(
                asin=book.asin,
                price=book.price,
                be_acos=book.be_acos,
                reviews=book.reviews,
            )
            for book in current_profile.book_set.all()  # type:ignore
        }
        if be_acos_per_book is None:
            pass

        campaigns_to_update = []
        managed_campaigns = (
            Campaign.objects.filter(
                profile=current_profile,
                managed=True,
                state=SpState.ENABLED.value,
                last_updated_date_on_amazon__lt=mod_limit_epoch_ms,
                sponsoring_type="sponsoredProducts",
            )
            .exclude(campaign_name__contains="-GP-")
            .exclude(campaign_purpose=CampaignPurpose.GP)
            .exclude(campaign_purpose=CampaignPurpose.Auto_GP)
        )
        if not managed_campaigns.exists():
            continue
        campaign_data = (
            RecentReportData.objects.filter(
                report_type=SpReportType.PLACEMENT,
                campaign__profile=current_profile,
                campaign__managed=True,
            )
            .exclude(campaign__campaign_name__contains="-GP-")
            .exclude(campaign__campaign_purpose=CampaignPurpose.GP)
            .exclude(campaign__campaign_purpose=CampaignPurpose.Auto_GP)
        ).order_by("-date")
        if not campaign_data.exists():
            continue
        # create a dictionary with all the campaign data aggregated for all managed campaigns
        campaign_data_mem_tos: Dict[int, AdSlice] = {}
        campaign_data_mem_pp: Dict[int, AdSlice] = {}
        for datum in campaign_data:
            campaign_id = getattr(datum, "campaign_id")
            if datum.placement == PlacementsOnAmazon.TOS:
                campaign_data_mem_tos = _process_report_datum(
                    datum=datum,
                    datum_id=campaign_id,
                    data_mem=campaign_data_mem_tos,
                    date_min_data=date_min_data,
                )
            elif datum.placement == PlacementsOnAmazon.PP:
                campaign_data_mem_pp = _process_report_datum(
                    datum=datum,
                    datum_id=campaign_id,
                    data_mem=campaign_data_mem_pp,
                    date_min_data=date_min_data,
                )
            else:
                continue

        for current_campaign in managed_campaigns:
            campaign_id = getattr(current_campaign, "id")
            # get the real break even acos
            book_price = DEFAULT_BOOK_PRICE
            try:
                asin = current_campaign.asins[0]
                be_acos = be_acos_per_book[asin].be_acos if asin in be_acos_per_book else DEFAULT_BE_ACOS
                book_price = be_acos_per_book[asin].price if asin in be_acos_per_book else DEFAULT_BOOK_PRICE
            except:
                be_acos = DEFAULT_BE_ACOS
            adjustments = []
            for campaign_data_mem, placement_type_mult, predicate in [
                (
                    campaign_data_mem_tos,
                    "placement_tos_mult",
                    SponsoredProductsPlacement.PLACEMENT_TOP,
                ),
                (
                    campaign_data_mem_pp,
                    "placement_pp_mult",
                    SponsoredProductsPlacement.PLACEMENT_PRODUCT_PAGE,
                ),
            ]:
                ad_slice = (
                    campaign_data_mem[campaign_id]
                    if campaign_id in campaign_data_mem
                    else AdSlice(0.0, 0.0, 0, 0, 0, 0)
                )
                current_placement_mult = getattr(current_campaign, placement_type_mult)
                placement_change, pause = _campaign_adjust(
                    slice=ad_slice,
                    target_acos=be_acos,
                    current_val=current_placement_mult,
                    book_price=book_price,
                )
                if placement_change != 0:
                    adjustments.append(
                        PlacementBidding(
                            percentage=current_placement_mult + placement_change,
                            placement=predicate,
                        )
                    )
            if len(adjustments) > 0:
                campaigns_to_update.append(
                    CampaignEntity(
                        external_id=current_campaign.campaign_id_amazon,
                        dynamic_bidding=DynamicBidding(placement_bidding=adjustments),
                    ).dict(exclude_none=True, by_alias=True)
                )
        # execute the update function
        if len(campaigns_to_update) > 0:
            campaign_adapter = CampaignAdapter(current_profile)
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
            # print(f"Updated {len(campaigns_to_update)} campaign placements on {current_profile.nickname} [{current_profile.country_code}]")


def _process_report_datum(datum, datum_id, data_mem, date_min_data):
    """Helper function to create or add key report data for keywords, targets, placements"""
    if datum_id in data_mem:
        single_entry_data = data_mem[datum_id]
        # check if sufficient data has been gathered, if not, add more data to the mem storage
        datum_date = getattr(datum, "date")
        entry_orders = float(getattr(single_entry_data, "orders"))
        if datum_date >= date_min_data or entry_orders < MIN_SALES_FOR_BID_CHANGE_DATA:
            for metric in AdSlice.__dataclass_fields__:
                updated_val = getattr(single_entry_data, metric) + float(getattr(datum, metric))
                setattr(single_entry_data, metric, updated_val)
            data_mem[datum_id] = single_entry_data
    else:
        data_mem[datum_id] = AdSlice(
            float(datum.sales),
            float(datum.spend),
            datum.kenp_royalties,
            datum.impressions,
            datum.clicks,
            datum.orders,
        )
    return data_mem


def create_multiple_sp_product_ads(
    campaigns: List[Campaign],
    ad_groups: List[AdGroup],
    asins: List[str],
    server: str,
    profile_id: int,
):
    """Create a product ad per ad group."""
    for campaign, ad_group, asin in zip(campaigns, ad_groups, asins):
        new_product_ad_info = dict(
            campaignId=campaign.campaign_id_amazon,
            adGroupId=ad_group.ad_group_id,
            asin=asin,
            state=SpState.ENABLED.value,
        )

        # can't create multiple product ads at once, since the Amazon API may
        # return product ads in a different order than the request
        new_product_ad_resp = AdsAPI.add_sp_data(
            server=server,
            profile_id=profile_id,
            data_dicts_array=[new_product_ad_info],
            endpoint=SpEndpoint.PRODUCT_ADS,
        )
        if not new_product_ad_resp or not isinstance(new_product_ad_resp, list):
            _logger.error(
                "Failed to create product ad on profile %s for campaign: %s",
                profile_id,
                campaign.campaign_id_amazon,
            )
            return
        # only one product ad is created per request
        new_product_ad_id = new_product_ad_resp[0].get("adId")
        if not new_product_ad_id:
            _logger.error(
                "Failed to create product ad on profile %s in campaign %s"
                " in ad group %s for ASIN %s; got the following response: %s",
                profile_id,
                campaign.campaign_id_amazon,
                ad_group.ad_group_id,
                asin,
                new_product_ad_resp,
            )
            return
        # store the new ad group details in the DB
        ProductAd.objects.create(
            campaign=campaign,
            ad_group=ad_group,
            product_ad_id=int(new_product_ad_id),
            asin=asin,
        )


def create_multiple_sp_campaigns(
    books: List[Book],
    campaign_purpose: str,
    tos: Optional[int] = None,
    pp: Optional[int] = None,
    bidding_strategy: Optional[BiddingStrategies] = BiddingStrategies.DOWN_ONLY,
    default_bid: Optional[float] = DEFAULT_BID,
) -> Dict[Book, AdGroup]:
    """
    Create multiple sp campaigns with a specified purpose on a profile
    Optional arguments: tos & pp are for Top of Search and Product Pages multipliers
    """
    raise NotImplemented("Needs refactoring")
    campaigns_request_data = {}

    for book in books:
        build_campaign_service = BuildCampaignEntityService(
            campaign_purpose=campaign_purpose,
            book=book,
            bidding_strategy=bidding_strategy,
            tos=tos,
            pp=pp,
        )
        campaign = build_campaign_service.build()

        # grouping campaigns by profiles, which are grouped by servers
        existing_server_campaigns = campaigns_request_data.get(book.profile.profile_server, {})
        existing_profile_campaigns = existing_server_campaigns.get(book.profile, [])
        existing_profile_campaigns.append({"data": campaign, "book": book})
        existing_server_campaigns[book.profile] = existing_profile_campaigns
        campaigns_request_data[book.profile.profile_server] = existing_server_campaigns

    result_ad_groups = _get_ad_groups_for_campaigns(campaigns_request_data, default_bid, targeting_type)

    return result_ad_groups


def _get_ad_groups_for_campaigns(
    campaigns_request_data: Dict[str, Dict[Profile, List[Dict[str, Book]]]],
    default_bid: float,
    targeting_type: str,
):
    result_ad_groups = {}
    for server, server_profiles in campaigns_request_data.items():
        for profile, profile_campaigns in server_profiles.items():
            data = [campaign["data"] for campaign in profile_campaigns]
            # create the campaigns through the API
            # response = AdsAPI.add_sp_data(
            #     server=server,
            #     profile_id=profile.profile_id,
            #     data_dicts_array=data,
            #     endpoint=SpEndpoint.CAMPAIGNS,
            # )

            if not response or not isinstance(response, list):
                _logger.error(
                    "Got the following campaign creation response which caused an error: %s",
                    response,
                )
                continue

            if len(response) != len(profile_campaigns):
                _logger.error(
                    "Campaign creation response length does not match the number of campaigns requested"
                )
                continue

            created_campaigns = _create_campaign_objects_from_api_response(
                profile_campaigns, profile, response, targeting_type
            )
            ad_group_adapter = AdGroupAdapter(profile)
            ad_groups_entities = [
                AdGroupEntity(name=campaign.campaign_name, campaign_id=campaign.campaign_id_amazon).dict(
                    by_alias=True, exclude={"external_id"}
                )
                for campaign in created_campaigns
            ]
            # FIXME: nothing is done with the failed ad groups
            created, failed = ad_group_adapter.batch_create(ad_groups_entities)
            # todo save created adgroups in db
            # create ad groups for each campaign
            # ad_groups = create_multiple_sp_ad_groups(
            #     campaigns=created_campaigns,
            #     server=server,
            #     profile_id=profile.profile_id,
            #     default_bid=default_bid,
            # )

            if not created:
                _logger.error(
                    "Failed to create ad groups for campaigns on profile %s",
                    profile.profile_id,
                )
                continue
            create_multiple_sp_product_ads(
                campaigns=created_campaigns,
                ad_groups=AdGroup.objects.filter(ad_group_id__in=created),
                asins=[campaign["book"].asin for campaign in profile_campaigns],
                server=server,
                profile_id=profile.profile_id,
            )

            for campaign, ad_group in zip(profile_campaigns, ad_groups):
                result_ad_groups[campaign["book"]] = ad_group
    return result_ad_groups


def _create_new_campaign_name(book: Book, book_title_acronym: str, campaign_purpose: str, profile: Profile):
    existing_campaigns = Campaign.objects.filter(
        asins__contains=[book.asin],
        profile=profile,
        campaign_name__contains=campaign_purpose,
        sponsoring_type="sponsoredProducts",
    )
    campaign_count = str(existing_campaigns.count() + 1)
    new_campaign_name = "-".join(
        (
            book_title_acronym,
            "SP",
            campaign_purpose,
            campaign_count,
            book.asin,
            book.format.split(sep=" ")[0],
        )
    )  # Result e.g.: ABCDE-SP-Broad-Research-5-000ASIN000-Paperback
    return new_campaign_name


def _create_campaign_objects_from_api_response(
    profile_campaigns: List[Dict],
    profile: Profile,
    response: List[Dict],
    targeting_type: str,
) -> List[Campaign]:
    created_campaigns = []
    for campaign, campaign_response in zip(profile_campaigns, response):
        if not campaign_response or not campaign_response.get("campaignId"):
            _logger.error(
                "Got the following campaign creation response which caused an error: %s",
                campaign_response,
            )
            continue
        campaign_id = campaign_response["campaignId"]
        # can't use bulk_create because pk won't be set
        created_campaign = Campaign.objects.create(
            campaign_id_amazon=campaign_id,
            profile=profile,
            targeting_type=targeting_type,
            campaign_name=campaign["data"]["name"],
            managed=True,
            asins=[
                campaign["book"].asin,
            ],
        )
        created_campaigns.append(created_campaign)

    return created_campaigns


def _start_date_to_string(country_code: str) -> str:
    """Returns campaign start date as today, allowing for countries ahead of GMT"""
    now = datetime.today()
    if country_code in TIME_LIMITS and now.hour >= TIME_LIMITS[country_code]:
        now = now + timedelta(days=1)
    date_as_string = now.strftime("%Y%m%d")
    return date_as_string


@app.task
def fill_out_associated_sp_campaigns_in_book_model(server=None, profile_ids: Optional[list[int]] = None):
    """Fill out or Create the missing campaigns per Book for managed profiles, campaigns and books"""
    if profile_ids:
        profiles = Profile.objects.filter(id__in=profile_ids)
    # Make sure the ASINs sync function is run before this one
    else:
        profiles = Profile.objects.filter(managed=True)
    if not profiles.exists():
        return
    if server:
        profiles = profiles.filter(profile_server=server)
    for current_profile in profiles:
        server = current_profile.profile_server
        managed_books = Book.objects.filter(managed=True, profile=current_profile)
        if not managed_books.exists():
            continue
        # for each managed book in profile
        for current_book in managed_books:
            book_campaigns_db = Campaign.objects.filter(
                Q(serving_status=CampaignServingStatus.CAMPAIGN_STATUS_ENABLED.value)
                | Q(serving_status=CampaignServingStatus.CAMPAIGN_OUT_OF_BUDGET.value)
                | Q(serving_status=CampaignServingStatus.ADVERTISER_PAYMENT_FAILURE.value),
                profile=current_profile,
                asins__contains=[current_book.asin],
                sponsoring_type="sponsoredProducts",
            )
            bool(book_campaigns_db)
            for campaign_purpose, book_model_field in [
                ("Exact-Scale", "campaign_scale_kw"),
                ("Product-Comp", "campaign_scale_asin"),
            ]:  # PURPOSE_BOOK_MODEL_MAP.items():
                if campaign_purpose in ["Cat-Research", "Broad-Research"]:
                    continue
                current_campaign = getattr(current_book, book_model_field)
                campaign_to_assign = _handle_campaign(
                    # current_profile=current_profile,
                    # current_book=current_book,
                    campaign_purpose=campaign_purpose,
                    current_campaign=current_campaign,
                    book_campaigns_db=book_campaigns_db,
                )
                if current_campaign != campaign_to_assign:
                    setattr(current_book, book_model_field, campaign_to_assign)
            current_book.save()


def _handle_campaign(
    # current_profile: Profile,
    # current_book: Book,
    campaign_purpose: str,
    current_campaign: Campaign,
    book_campaigns_db,
) -> Campaign:
    """Find an existing campaign to fill out the Book model campaign mapping, no creation step"""
    # set the right model to be used in filtering
    if campaign_purpose in ["Broad-Research", "Exact-Scale", "GP"]:
        model = Keyword
        filter = Count(
            "keyword",
            filter=Q(keyword__state=SpState.ENABLED.value) & Q(keyword__keyword_type="Positive"),
        )
    else:
        model = Target
        filter = Count(
            "target",
            filter=Q(target__state=SpState.ENABLED.value) & Q(target__keyword_type="Positive"),
        )
    campaign_max_targets = CAMPAIGN_MAX_TARGETS_MAP[campaign_purpose]

    # if current_campaign is blank then perhaps it's in the DB already
    if current_campaign and current_campaign.state == SpState.ENABLED.value:
        if campaign_purpose == "Auto-Discovery":
            return current_campaign
        # check for the number of keywords in the campaign already assigned in the Book model, create a new one if necessary
        enabled_count = model.objects.filter(
            campaign=current_campaign,
            state=SpState.ENABLED.value,
            keyword_type="Positive",
        ).count()
        if enabled_count < campaign_max_targets:
            return current_campaign
    else:
        # if there are already campaigns in the DB and active then search for a relevant one
        matching_purpose_campaigns = (
            book_campaigns_db.filter(
                Q(campaign_name__contains=campaign_purpose) | Q(campaign_purpose=campaign_purpose)
            )
            .exclude(campaign_name__contains="Product-Own")
            .exclude(campaign_name__contains="Single")
        )
        if matching_purpose_campaigns.count() > 0:
            # check that the number of keywords or targets in the campaigns are sufficiently low
            filtered_campaigns_all = (
                matching_purpose_campaigns.annotate(enabled_count=filter)
                .exclude(enabled_count=0)
                .order_by("enabled_count")
            )
            if filtered_campaigns_all.count() > 0:
                filtered_campaign = filtered_campaigns_all[0]
                enabled_count = filtered_campaign.enabled_count
                if enabled_count < campaign_max_targets:
                    # set the found campaigns to the current campaign and save in DB
                    return filtered_campaign
    # 2022.05.21 removed new campaign creation code to prevent "Incomplete" campaigns
    # new campaign creation code
    # new_campaign_entry, new_ad_group = create_sp_campaign(
    #     book=current_book, campaign_purpose=campaign_purpose, profile=current_profile
    # )
    # if not new_campaign_entry or not new_ad_group:
    #     return current_campaign
    return current_campaign


def fill_out_sp_negatives(server=None):
    """Fill out negative keywords and targets in all ad groups per managed book"""
    raise NotImplemented("Need refactoring")
    # if a keyword has been added as a negative to 1 ad group or 1 campaign
    # then it should be added to other ad groups in Auto & Broad & Cats campaigns for that book
    managed_profiles = _get_managed_profiles(server=server)
    if not managed_profiles.exists():
        return
    # get a list of negatives per book
    # negatives may be scattered randomly among several ad groups
    # API requests must be submitted per profile, per query type (search terms & targets)
    books_per_profile = {
        profile: profile.book_set.filter(managed=True)  # this should be a QuerySet of Books
        for profile in managed_profiles
        if profile.book_set.filter(managed=True).exists()
    }
    for current_profile, profile_books in books_per_profile.items():
        for query in QUERY_TYPES:  # looping through search terms then targets
            # get negative queries for each book in profile
            negatives_per_book = _get_negatives_per_book(
                profile=current_profile, profile_books=profile_books, query=query
            )
            _add_sp_keywords_per_book(
                profile=current_profile,
                keywords_per_book_per_profile=negatives_per_book,
                endpoint=query.neg_endpoint,
            )


def _get_negatives_per_book(profile: Profile, profile_books, query: QueryData) -> Dict[str, List[str]]:
    """Gets negative keywords and targets for a QuerySet of books"""
    if query.query_report == SpReportType.KEYWORD_QUERY:
        model = Keyword
        filter_by = "keyword_text"
    else:
        model = Target
        filter_by = "resolved_expression_text"
    model_filters = dict(keyword_type="Negative", campaign__profile=profile, state=SpState.ENABLED.value)
    negatives_per_book = {
        book.asin: list(
            model.objects.filter(campaign__asins__contains=[book.asin], **model_filters)
            .order_by(filter_by)
            .values_list(filter_by, flat=True)
            .distinct(filter_by)
        )
        for book in profile_books
        if model.objects.filter(campaign__asins__contains=[book.asin], **model_filters).exists()
    }
    return negatives_per_book


def archive_never_negatives():
    """Archives enabled search terms foundin the never negatives list per book in profile"""
    pass


def _get_positive_exacts_per_book(
    profile: Profile,
    profile_books,
    query: QueryData,
    campaign_name_snippet: Optional[str] = None,
) -> Dict[str, List[str]]:
    """Gets positives keywords and targets for a QuerySet of books"""
    model_filters = dict(
        keyword_type="Positive",
        campaign__profile=profile,
        state=SpState.ENABLED.value,
        serving_status__in=TARGETS_VALID_STATUSES,
    )
    if query.query_report == SpReportType.KEYWORD_QUERY:
        model = Keyword
        filter_by = "keyword_text"
        model_filters["match_type"] = "exact"
    else:
        model = Target
        filter_by = "resolved_expression_text"
        model_filters["targeting_type"] = SpExpressionType.MANUAL.value
    if campaign_name_snippet is not None:
        model_filters["campaign__campaign_name__contains"] = campaign_name_snippet
    positives_per_book = {
        book.asin: list(
            model.objects.filter(campaign__asins__contains=[book.asin], **model_filters)
            .order_by(filter_by)
            .values_list(filter_by, flat=True)
            .distinct(filter_by)
        )
        for book in profile_books
        if model.objects.filter(campaign__asins__contains=[book.asin], **model_filters).exists()
    }
    return positives_per_book


def _sort_asins(all_unique_keywords, query_report):
    """Helper function to remove asins or keywords"""
    unique_keywords = []
    if query_report == SpReportType.TARGET_QUERY:
        # keep asins
        for kw in all_unique_keywords:
            if len(kw) == 10 and " " not in kw:
                unique_keywords.append(kw)
    else:
        # keep keywords
        for kw in all_unique_keywords:
            if (len(kw) != 10 and len(kw) != 0) or " " in kw:
                unique_keywords.append(kw)
    return unique_keywords


def _move_search_terms(
    profile: Profile,
    book_data: List[BookData],
    # date_from: datetime,
    # date_to: datetime,
    query: QueryData,
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Analyse book data on a search term level creating a list of positive and negative search terms to be applied to a profile"""
    # initiate Dicts to hold positive and negative keywords
    profile_positives: Dict[str, List[str]] = {}
    profile_negatives: Dict[str, List[str]] = {}

    for asin, price, be_acos, _ in book_data:
        # initialise positive and negative keywords / targets Lists to be passed onto the generator Class and then onto POST request
        positives: List[str] = []
        negatives: List[str] = []
        # get search term (query) data for ASIN
        query_data = RecentReportData.objects.filter(
            # report_type=query.query_report,
            campaign__asins__contains=[asin],
            campaign__profile=profile,
            # date__gte=date_from,
            # date__lte=date_to,
        )
        if not query_data.exists():
            continue
        # returns an iterable Queryset of keywords / targets
        all_unique_keywords = list(
            query_data.order_by("query").values_list("query", flat=True).distinct("query")
        )
        unique_keywords = _sort_asins(all_unique_keywords, query.query_report)
        if len(unique_keywords) == 0:
            continue
        book = Book.objects.filter(asin=asin, profile=profile)
        # get existing negatives per asin to prevent multiple DB calls
        # returns a QuerySet flat list
        existing_negatives = _get_negatives_per_book(profile=profile, profile_books=book, query=query)
        existing_positive_exacts = _get_positive_exacts_per_book(
            profile=profile, profile_books=book, query=query
        )
        for current_keyword in unique_keywords:
            # if keyword is already in local negative keywords DB for this asin skip it, it should not be added as a negative or positive
            # even if it's not in all ad groups, it'll be propagated by the fill out negatives function:
            # def fill_out_sp_negatives():
            # Also check if the current keyword is already a keyword / target (after the OR)
            if current_keyword in existing_negatives.get(
                asin, []
            ) or current_keyword in existing_positive_exacts.get(asin, []):
                continue
            # check against criteria to see if the search term graduates
            # get the search term's aggregate sales, spend => ACOS
            current_query = _sum_report_data(
                query_data=query_data, query_data_filters=dict(query=current_keyword)
            )
            positives, negatives = _process_search_term(
                price, be_acos, positives, negatives, current_keyword, current_query
            )

        # Add the positives list per asin to the profile positives list
        if len(positives) > 0:
            # Execute addition of negatives on profile
            profile_positives[asin] = positives
        # Add the negatives list per asin to the profile negatives list
        if len(negatives) > 0:
            profile_negatives[asin] = negatives

    return profile_positives, profile_negatives


def _process_search_term(price, be_acos, positives, negatives, current_keyword, current_query: AdSlice):
    """Applies logic and actions to search terms"""
    if (
        current_query.kenp_royalties > current_query.spend
        and current_query.kenp_royalties > MIN_KENP_ROYALTIES_MULTIPLIER * float(price)
    ):
        positives.append(current_keyword)
        return positives, negatives
    elif current_query.kenp_royalties > 0:
        current_query.spend = current_query.spend - float(current_query.kenp_royalties)
    if current_query.sales > 0:
        acos = current_query.spend / current_query.sales
        if current_query.sales > (price * MIN_ORDERS_ST_GRADUATION):
            if acos < be_acos:
                # search term has proven to be profitable
                # -> graduate search term
                positives.append(current_keyword)
            else:
                # search term acos is too high
                # -> add search term as negative for that book on profile
                negatives.append(current_keyword)
                # else:
                # sales are between zero and price, not sure which way things will go, do nothing
    elif current_query.spend > price:
        # spent more than the book price with zero sales
        # -> add search term as a negative
        negatives.append(current_keyword)
    return positives, negatives


class BodyDict:
    """Helper class used to create the body arguments for POST requests to keywords and targets endpoints"""

    def __init__(
        self,
        endpoint: SpEndpoint,
        campaign_id: str,
        ad_group_id: str,
        target_text: str,
        bid: Optional[float] = None,
        match_type: Optional[str] = None,
    ):
        self.value = {
            "campaignId": campaign_id,
            "adGroupId": ad_group_id,
            "state": SpState.ENABLED.value,
        }
        if endpoint == SpEndpoint.KEYWORDS:
            self.value["keywordText"] = target_text
            if match_type:
                match_type = match_type.lower()
            self.value["matchType"] = (
                match_type if match_type in [MatchType.BROAD.value, MatchType.PHRASE.value] else "exact"
            )
        elif endpoint == SpEndpoint.NEGATIVE_KEYWORDS:
            self.value["keywordText"] = target_text
            self.value["matchType"] = (
                NegativeMatchType.PHRASE.value
                if match_type == MatchType.PHRASE.value
                else NegativeMatchType.EXACT.value
            )
        elif endpoint in [SpEndpoint.TARGETS, SpEndpoint.NEGATIVE_TARGETS]:
            self.value["expression"] = [
                {
                    "value": target_text,
                    "type": TargetingExpressionPredicateType.ASIN_SAME_AS.value,
                }
            ]  # type: ignore
            self.value["expressionType"] = SpExpressionType.MANUAL.value
        if bid:
            self.value["bid"] = bid  # type: ignore
        # if endpoint in [SpEndpoint.KEYWORDS, SpEndpoint.TARGETS]:
        #     if tos is not None or pp is not None:
        #         adjustments = []
        #         if tos is not None:
        #             adjustments.append({"predicate": "placementTop", "percentage": tos})
        #         if pp is not None:
        #             adjustments.append({"predicate": "placementProductPage", "percentage": pp})
        #         self.value["bidding"] = {"adjustments": adjustments}  # type: ignore


def _set_keyword_filters(endpoint: SpEndpoint):
    """Helper function to set the filters to the Keyword / Target models based on endpoint string"""
    if endpoint in [SpEndpoint.KEYWORDS, SpEndpoint.NEGATIVE_KEYWORDS]:
        model = Keyword
        identifier = "keyword_text"
    elif endpoint in [SpEndpoint.TARGETS, SpEndpoint.NEGATIVE_TARGETS]:
        model = Target
        identifier = "resolved_expression_text"
    else:
        _logger.error(
            "Unexpected endpoint: %s, passed to _add_sp_keywords_per_book's _set_keyword_filters fuction",
            endpoint,
        )
        return None, None, None
    if endpoint in [SpEndpoint.NEGATIVE_KEYWORDS, SpEndpoint.NEGATIVE_TARGETS]:
        keyword_type = "Negative"
    else:
        keyword_type = "Positive"
    return model, identifier, keyword_type


def _add_sp_keywords_per_book(
    profile: Profile,
    keywords_per_book_per_profile: Dict[str, List[str]],
    endpoint: SpEndpoint,
) -> None:
    """Adds positive and negative keywords and targets to ad groups, and create new campaigns if necessary"""
    server = profile.profile_server
    profile_ad_groups, campaign_purpose, assigned_campaign = _set_ad_group_filters(endpoint, profile)
    campaign_max_targets = CAMPAIGN_MAX_TARGETS_MAP[campaign_purpose]
    if not profile_ad_groups.exists():
        return
    keywords_array = []
    model, identifier, keyword_type = _set_keyword_filters(endpoint=endpoint)
    if not model or not identifier or not keyword_type:
        _logger.info(
            "Count not identify model, identifier, keyword_type for profile: %s [%s]",
            profile.nickname,
            profile.country_code,
        )
        return

    asins = list(keywords_per_book_per_profile.keys())
    all_profile_ad_groups_with_asins = list(
        profile_ad_groups.filter(campaign__asins__overlap=asins)
        .filter(
            Q(campaign__campaign_purpose=CampaignPurpose.Broad_Research)
            | Q(campaign__campaign_purpose=CampaignPurpose.Broad_Research_Single)
            | Q(campaign__campaign_name__contains="Broad-Research")
            | Q(campaign__campaign_purpose__contains=CampaignPurpose.Discovery)
        )
        .prefetch_related("campaign")
    )
    books = list(Book.objects.filter(asin__in=asins, profile=profile).prefetch_related("profile"))
    books_dict = {book.asin: book for book in books}

    keywords_per_ad_group_to_add: Dict[AdGroup, List[str]] = {}
    books_with_keywords_chunks = {}
    for asin, keywords in keywords_per_book_per_profile.items():
        # if negatives then get the ad groups where the ASIN exists and campaign
        # has Auto or Broad purpose add all keywords to ad groups
        if endpoint in NEGATIVE_ENDPOINTS:
            profile_ad_groups_with_asin = [
                ad_group for ad_group in all_profile_ad_groups_with_asins if asin in ad_group.campaign.asins
            ]
            # create a dictionary of ad_group and keywords (keywords will be all the same for negatives) so that multiple campaigns may be created for positives
            for ad_group in profile_ad_groups_with_asin:
                keywords_per_ad_group_to_add[ad_group] = keywords
        # if positives
        # add groups of keywords to several ad groups
        else:
            # Get assigned Exact-Scale or Product-Comp campaign
            book = books_dict.get(asin)
            # see if there is a scale campaign and offload some of the keywords to that scale campaign, if there's room
            scale_campaign = getattr(book, assigned_campaign)
            if scale_campaign:
                # Get singular ad group of that campaign
                ad_group_in_scale = scale_campaign.ad_groups.first()
                if ad_group_in_scale:
                    # Get number of enabled targets
                    positive_targets = model.objects.filter(
                        ad_group_id=ad_group_in_scale.ad_group_id,
                        keyword_type=keyword_type,
                        state=SpState.ENABLED.value,
                    )
                    targets_room = campaign_max_targets - positive_targets.count()
                    if targets_room >= 1:
                        # only add the number of keywords there's space for, the others will be added later
                        keywords_per_ad_group_to_add[ad_group_in_scale] = keywords[:targets_room]
                        keywords = keywords[targets_room:]
            # check if there are any keywords to assign to new campaigns
            if len(keywords) > 0:
                keywords_chunks = list(chunker(keywords, campaign_max_targets))
                books_with_keywords_chunks[book] = {
                    "keywords_chunks": keywords_chunks,
                }

    # create new campaigns and ad groups for each book and add the keywords to
    # the ad groups. Keywords are split into chunks, so campaigns and ad groups
    # are created for each chunk.
    max_chunks_length = max(
        [len(book_chunks["keywords_chunks"]) for book_chunks in books_with_keywords_chunks.values()],
        default=0,
    )
    while max_chunks_length > 0:
        books = list(books_with_keywords_chunks.keys())
        ad_groups_per_book = create_multiple_sp_campaigns(books=books, campaign_purpose=campaign_purpose)
        for book, ad_group in ad_groups_per_book.items():
            keywords_chunks = books_with_keywords_chunks[book]["keywords_chunks"]
            if len(keywords_chunks) > 0:
                # add the first chunk of keywords to the ad group
                keywords_per_ad_group_to_add[ad_group] = keywords_chunks.pop(0)
            if len(keywords_chunks) <= 0:
                # remove the book from the dictionary if there are no more chunks
                books_with_keywords_chunks.pop(book, None)

        max_chunks_length = max(
            [len(book["keywords_chunks"]) for book in books_with_keywords_chunks.values()],
            default=0,
        )
    # loop through the list of keywords to create the list of dicts to be passed in the POST request to Amazon
    for ad_group, keywords_list in keywords_per_ad_group_to_add.items():
        ad_group_id = ad_group.ad_group_id
        campaign_id = ad_group.campaign.campaign_id_amazon
        if endpoint in NEGATIVE_ENDPOINTS:
            # check that target is not in relevant endpoint of ad group already
            existing_targets = (
                model.objects.filter(
                    campaign__profile=profile,
                    ad_group_id=ad_group_id,
                    keyword_type=keyword_type,
                )
                .order_by(identifier)
                .values_list(identifier, flat=True)
                .distinct(identifier)
            )
            bool(existing_targets)
        else:
            existing_targets = []
        targets_added = 0
        for target in keywords_list:
            if target in existing_targets:
                continue
            request_body = BodyDict(
                endpoint=endpoint,
                campaign_id=campaign_id,
                ad_group_id=ad_group_id,
                target_text=target,
            )
            keywords_array.append(request_body.value)
            targets_added += 1

    # the request below adds targets to any ad group specified, even multiple ad groups
    # so it needs to be run on a per endpoint itteration
    if len(keywords_array) > 0:
        AdsAPI.add_sp_data(
            server=server,
            profile_id=profile.profile_id,
            data_dicts_array=keywords_array,
            endpoint=endpoint,
        )


def _set_ad_group_filters(endpoint: SpEndpoint, profile: Profile):
    # filter by the type of ad groups so as not to add keywords to product targeting ad groups and vice versa
    profile_ad_groups_both_types = AdGroup.objects.filter(
        campaign__profile=profile,
        campaign__managed=True,
        campaign__serving_status=CampaignServingStatus.CAMPAIGN_STATUS_ENABLED.value,
        state=SpState.ENABLED.value,
    )
    if endpoint in KEYWORD_ENDPOINTS:
        profile_ad_groups = profile_ad_groups_both_types.filter(
            Q(manual_type="Keyword") | Q(campaign__targeting_type=CampaignTargetingType.AUTO.value)
        )
        campaign_purpose = "Exact-Scale"
        assigned_campaign = "campaign_scale_kw"
    else:
        profile_ad_groups = profile_ad_groups_both_types.filter(
            Q(manual_type="Product") | Q(campaign__targeting_type=CampaignTargetingType.AUTO.value)
        )
        campaign_purpose = "Product-Comp"
        assigned_campaign = "campaign_scale_asin"
    return profile_ad_groups, campaign_purpose, assigned_campaign


@app.task
def sp_data_sync_days_failure():
    _logger.info("sp_data_sync_days_failure is started")

    reports = (
        Report.objects.filter(
            report_status__contains="FAILURE",
        )
        .values_list(
            "report_type",
            "profile_id",
            "report_server",
            "report_for_date",
        )
        .iterator()
    )

    reports_count = Report.objects.filter(report_status__contains="FAILURE").count()

    _logger.info("Reports with failure status before - %s", reports_count)

    for report in reports:
        report_type, profile_id, report_server, report_for_date = report

        report_info = AdsAPI.run_sp_report(
            server=report_server,
            profile_id=profile_id,
            record_type=report_type,
            report_date=report_for_date,
        )

        if not report_info:
            _logger.info(
                "No report_info for profile: %s, report_type: %s, report_server: %s, date: %s",
                profile_id,
                report_type,
                report_server,
                report_for_date,
            )
            continue

        time.sleep(0.3)
        # save report for later retrieval
        Report.objects.update_or_create(
            report_id=report_info.get("reportId"),
            defaults={
                "profile_id": profile_id,
                "report_type": report_type,
                "report_status": report_info.get("status"),
                "report_for_date": report_for_date,
                "report_server": report_server,
            },
        )

    reports_count = Report.objects.filter(report_status__contains="FAILURE").count()

    _logger.info("Reports with failure status after - %s", reports_count)
    _logger.info("sp_data_sync_days_failure is complete")


@app.task
def classify_ad_groups(profile_ids: Optional[QuerySet[Profile]] = None):
    """Classify ad groups as Keyword or Product types"""

    custom_filter = {"manual_type": ""}
    if profile_ids:
        profiles = Profile.objects.filter(id__in=profile_ids)
        custom_filter["campaign__profile__in"] = profiles  # type: ignore

    ad_groups_to_classify = AdGroup.objects.filter(**custom_filter).exclude(
        serving_status=ProductAdServingStatus.AD_POLICING_SUSPENDED.value
    )  # .exclude(serving_status__contains="INCOMPLETE")

    if ad_groups_to_classify.count() == 0:
        return
    keyword_ad_groups = (
        Keyword.objects.all()
        .order_by("ad_group_id")
        .values_list("ad_group_id", flat=True)
        .distinct("ad_group_id")
    )
    bool(keyword_ad_groups)
    product_ad_groups = (
        Target.objects.all()
        .order_by("ad_group_id")
        .values_list("ad_group_id", flat=True)
        .distinct("ad_group_id")
    )
    bool(product_ad_groups)
    ad_groups_to_update = []
    for ad_group in ad_groups_to_classify:
        if ad_group.ad_group_id in keyword_ad_groups:
            ad_group.manual_type = "Keyword"
            ad_groups_to_update.append(ad_group)
        elif ad_group.ad_group_id in product_ad_groups:
            ad_group.manual_type = "Product"
            ad_groups_to_update.append(ad_group)
        for manual_type, purpose_list in CAMPAIGN_PURPOSE_TYPES.items():
            for purpose_iter in purpose_list:
                if purpose_iter in ad_group.ad_group_name:
                    ad_group.manual_type = manual_type
                    break
            if ad_group.manual_type != "":
                break
    if len(ad_groups_to_update) > 0:
        AdGroup.objects.bulk_update(ad_groups_to_update, ["manual_type"], batch_size=1000)


@app.task
def process_sp_queries(profile_pks: list[int]):
    """Graduate keywords and ASINs between campaigns and add negative search terms if necessary"""
    # Consider keywords fromt he last 30 days, excluding the last two days.
    _logger.info("process_sp_queries is started")
    raise NotImplementedError("should refactor _add_sp_keywords_per_book method")
    profiles_proccessed = []

    if not profile_pks:
        # Only run for managed managed_profiles
        managed_profiles = Profile.objects.filter(managed=True)
    else:
        managed_profiles = Profile.objects.filter(id__in=profile_pks)

    if not managed_profiles.exists():
        return

    _logger.info(
        "Profiles selected [(pk)] %s",
        list(managed_profiles.values_list("pk", flat=True)),
    )

    def _map_book_data(book_queryset) -> List[BookData]:
        """
        Get the book's break even ACOS using break even ACOS instead of target ACOS
        as with better control a search term's performance may be improved
        """
        return [
            BookData(
                asin=book.asin,
                price=book.price if book.price > 0.0 else DEFAULT_BOOK_PRICE,
                be_acos=book.be_acos if book.be_acos > 0.0 else DEFAULT_BE_ACOS,
                reviews=book.reviews if book.reviews else 0,
            )
            for book in book_queryset
        ]

    book_data_per_profile = {
        profile: _map_book_data(profile.book_set.filter(managed=True))
        for profile in managed_profiles
        if profile.book_set.filter(managed=True).exists()
    }

    # for each managed profile
    for current_profile, book_data in book_data_per_profile.items():
        try:
            for query in QUERY_TYPES:
                # For each Book, Get all search terms which fulfil a given criteria
                profile_positives, profile_negatives = _move_search_terms(
                    profile=current_profile,
                    book_data=book_data,
                    query=query,
                )
                # Note: the 2 if: statements below must be run within the "for query in query_types:" loop as the
                # Amazon API endpoint changes between keyword and target
                # Execute addition of positives on profile
                try:
                    if len(profile_positives) > 0:
                        _add_sp_keywords_per_book(
                            profile=current_profile,
                            keywords_per_book_per_profile=profile_positives,
                            endpoint=query.pos_endpoint,
                        )
                except Exception as e:
                    _logger.error(traceback.format_exc())
                    _logger.error(
                        "Error for profile[%s], query[%s]",
                        current_profile,
                        query.pos_endpoint,
                    )
                    _logger.error(e)
                else:
                    _logger.info(
                        "[%s][%s] %s positives processed",
                        current_profile,
                        query.pos_endpoint,
                        len(profile_positives),
                    )

                # Execute addition of negatives on profile
                try:
                    if len(profile_negatives) > 0:
                        _add_sp_keywords_per_book(
                            profile=current_profile,
                            keywords_per_book_per_profile=profile_negatives,
                            endpoint=query.neg_endpoint,
                        )
                except Exception as e:
                    _logger.error(e)
                    _logger.error(traceback.format_exc())
                    _logger.error(
                        "Error for profile[%s], query[%s]",
                        current_profile,
                        query.neg_endpoint,
                    )
                else:
                    _logger.info(
                        "[%s][%s] %s negatives processed",
                        current_profile,
                        query.neg_endpoint,
                        len(profile_positives),
                    )

        except Exception as e:
            _logger.error(e)
            _logger.error(traceback.format_exc())
            _logger.error("Error while processing profile [%s]", current_profile)
        else:
            profiles_proccessed.append(current_profile.pk)
    _logger.info(
        "process_sp_queries is comlete. Profiles were proccessed %s",
        profiles_proccessed,
    )


@app.task
def managed_campaigns_for_managed_books():
    """Syncs managed campaigns for managed books"""
    managed_asins = list(Book.objects.filter(managed=True).values_list("asin", flat=True).distinct("asin"))
    campaigns_to_be_managed = Campaign.objects.filter(
        asins__overlap=managed_asins, sponsoring_type="sponsoredProducts"
    )
    campaigns_to_not_manage = Campaign.objects.filter(
        managed=True, sponsoring_type="sponsoredProducts"
    ).exclude(asins__overlap=managed_asins)
    if campaigns_to_be_managed:
        campaigns_to_be_managed.update(managed=True)
    if campaigns_to_not_manage:
        campaigns_to_not_manage.update(managed=False)


@app.task
def reset_gp_bids(profile_pks: list[int]):
    """Reset's all GP campaign bids to the default minimum for managed campaigns"""
    if profile_pks:
        managed_profiles = Profile.objects.filter(id__in=profile_pks)
    else:
        managed_profiles = Profile.objects.filter(managed=True)

    for profile in managed_profiles:
        keywords_to_update = []
        keywords_adapter = KeywordsAdapter(profile)
        targets_adapter = TargetsAdapter(profile)

        keywords_ids = Keyword.objects.filter(
            Q(campaign__campaign_name__contains="_GP_")
            | Q(campaign__campaign_name__contains="-GP-")
            | Q(campaign__campaign_purpose=CampaignPurpose.GP),
            campaign__profile=profile,
            campaign__managed=True,
            serving_status__in=TARGETS_VALID_STATUSES,
            bid__gt=DEFAULT_MIN_BID,
        ).values_list("keyword_id", flat=True)

        for keyword_id in keywords_ids:
            keywords_to_update.append(
                KeywordEntity(external_id=keyword_id, bid=DEFAULT_MIN_BID).dict(
                    exclude_none=True, by_alias=True
                )
            )
        keywords_adapter.batch_update(keywords_to_update)
        _logger.info(
            "%s GP keywords floored on %s [%s]",
            len(keywords_to_update),
            profile.nickname,
            profile.country_code,
        )

        targets_to_update = []
        targets_ids = Target.objects.filter(
            Q(campaign__campaign_name__contains="Auto-GP-")
            | Q(campaign__campaign_purpose=CampaignPurpose.Auto_GP),
            campaign__profile=profile,
            campaign__managed=True,
            serving_status__in=TARGETS_VALID_STATUSES,
            bid__gt=DEFAULT_MIN_BID,
        ).values_list("target_id", flat=True)

        for target_id in targets_ids:
            targets_to_update.append(
                TargetEntity(external_id=target_id, bid=DEFAULT_MIN_BID).dict(
                    exclude_none=True, by_alias=True
                )
            )
        targets_adapter.batch_update(targets_to_update)

        _logger.info(
            "{%s Auto GP keywords floored on %s [%s]",
            len(targets_to_update),
            profile.nickname,
            profile.country_code,
        )

@app.task
def update_bids_for_managed():
    managed_profiles = Profile.objects.filter(managed=True)

    profile_entity_ids = defaultdict(lambda: defaultdict(list))
    for model in [Keyword, Target]:
        entity_id = 'keyword_id' if model == Keyword else 'target_id'
        entity_ids = model.objects.filter(
            campaign__profile__in=managed_profiles,
            campaign__managed=True,
            serving_status__in=TARGETS_VALID_STATUSES,
            bid__gte=DEFAULT_MAX_FILTER_BID
        ).values_list('campaign__profile__id', entity_id)

        for profile_id, entity_id in entity_ids:
            profile_entity_ids[profile_id][model].append(entity_id)

    for profile in managed_profiles:
        for model, entity_ids in profile_entity_ids[profile.id].items():
            update_entities(profile, model, entity_ids)

def update_entities(profile, model, entity_ids):
    entities_to_update = []

    if model == Keyword:
        entity_adapter = KeywordsAdapter(profile)
        EntityEntity = KeywordEntity
    elif model == Target:
        entity_adapter = TargetsAdapter(profile)
        EntityEntity = TargetEntity

    for entity_id in entity_ids:
        entities_to_update.append(
            EntityEntity(external_id=entity_id, bid=DEFAULT_MAX_BID).dict(
                exclude_none=True, by_alias=True
            )
        )

    if entities_to_update:
        entity_adapter.batch_update(entities_to_update)
        _logger.info(
            "%s Update %s maximum bid on profile %s [%s]",
            len(entities_to_update),
            model.__name__.lower(),
            profile.nickname,
            profile.country_code,
        )
    else:
        _logger.info(
            "No %s to update for profile %s [%s]",
            model.__name__.lower(),
            profile.nickname,
            profile.country_code,
        )

def remove_dupe_books_from_profile():
    profile = Profile.objects.get(nickname="Dylan", country_code="US")
    books = Book.objects.filter(profile=profile)
    for book in books:
        dupe_books = Book.objects.filter(profile=profile, asin=book.asin)
        if dupe_books.count() > 1:
            book.delete()


def set_campaigns_target_acos():
    """Updates campaigns with no target ACOS set to Break Even ACOS of book"""
    managed_profiles = _get_managed_profiles()
    if not managed_profiles:
        return
    book_data_per_profile = {}
    for profile in managed_profiles:  # type: ignore
        books_with_be_acos = profile.book_set.filter(be_acos__gt=0)
        book_data = {}
        for book in books_with_be_acos:
            book_data[book.asin] = book.be_acos
        book_data_per_profile[profile] = book_data

    books_with_be_acos = Book.objects.filter(be_acos__gt=0)
    list_of_asins = list(books_with_be_acos.values_list("asin", flat=True).distinct("asin"))
    campaigns_to_process = Campaign.objects.filter(target_acos=0, asins__overlap=list_of_asins)

    for campaign in campaigns_to_process:
        if campaign.profile not in book_data_per_profile:
            continue
        books_in_profile = book_data_per_profile[campaign.profile]
        if campaign.asins[0] in books_in_profile:
            campaign.target_acos = books_in_profile[campaign.asins[0]]
            campaign.save()


def do_json_request(
    url: str,
    headers: Dict[str, str],
    cookies: str,
    action_text: str,
    method: str = "GET",
    params=None,
    body=None,
):
    """Creates a retry session to do requests via requests library"""
    session = get_new_retry_session()
    if method == "GET":
        response = (
            session.get(url=url, headers=headers, cookies=cookies, params=params)
            if params
            else session.get(url=url, headers=headers, cookies=cookies)
        )
    elif method == "POST":
        response = session.post(url=url, headers=headers, cookies=cookies, json=body)
    elif method == "PUT":
        response = session.put(url=url, headers=headers, cookies=cookies, json=body)
    elif method == "PATCH":
        response = session.patch(url=url, headers=headers, cookies=cookies, json=body)
    else:
        raise NotImplementedError("Request method not implemented")
    try:
        response_json = response.json()
        return response_json
    except requests.exceptions.JSONDecodeError as e:
        if len(e.strerror) < 500:
            _logger.error("Error decoding JSON while %s: %s", action_text, e)
    except TypeError as e:
        _logger.error("Type error while %s: %s", action_text, e)
        return None


def read_cookies(seller: Optional[bool] = False) -> Dict[str, str]:
    """Reads the cookies.txt file to access Amazon thgough the console, Optionally get Seller Central cookies"""
    with open("cookies.txt", encoding="utf-8-sig") as f:
        cookies_txt = f.read()
    cookies = json.loads(cookies_txt)
    cookie_to_pop = "session-id" if seller is True else "__Host-mselc"
    for market, cookie_dict in cookies.items():
        if cookie_to_pop in cookie_dict:
            cookie_dict.pop(cookie_to_pop)
            cookies[market] = cookie_dict
    return cookies


def get_profile_info(entity_id: str, country_code: str):
    """Gets the profile info necessary to send requests using the Amazon Advertising console"""
    headers_profile_info = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
        "Accept": "*/*",
        "Accept-Language": "en-GB,en;q=0.5",
        "Content-Type": "application/json",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    cookies = read_cookies()
    domain = DOMAINS.get(country_code)
    url = f"https://advertising.amazon.{domain}/ups/user/info?entityId={entity_id}"

    cookies_to_send = cookies.get(country_code)
    if cookies_to_send is None:
        return None

    profile_info = do_json_request(
        url=url,
        headers=headers_profile_info,
        cookies=cookies_to_send,
        action_text="getting profile info",
        method="GET",
    )
    return profile_info

def get_asins(entity_id, country_code):
    return Book.objects.filter(
        profile__country_code=country_code,
        profile__entity_id=entity_id
    ).values_list('asin', flat=True)


def get_catalog_by_kdp(url, headers, cookies):
    all_books_on_amazon = []
    cursor_token = ""

    for page_index in range(CATALOG_PAGE_LIMIT):
        # no cursor toek in the UK
        payload = {
            "programType": "SP",
            "catalogType": "KDP",
            "pageIndex": page_index,
            "pageSize": 50,
            "additionalProductInfo": "ELIGIBILITY",
        }
        if cursor_token:
            payload["cursorToken"] = cursor_token
        # if len(cursor_token) > 0:
        #     url = f"https://advertising.amazon.{domain}/a9g-api/v2/products?programType=SP&vendorCodes=&catalogType=KDP&pageIndex={page_index}&pageSize=50&cursorToken={cursor_token}&additionalProductInfo=ELIGIBILITY"
        # else:
        #     url = f"https://advertising.amazon.{domain}/a9g-api/v2/products?programType=SP&vendorCodes=&catalogType=KDP&pageIndex={page_index}&pageSize=50&additionalProductInfo=ELIGIBILITY"
        try:
            response_from_amazon = do_json_request(
                url=url,
                headers=headers,
                params=payload,
                cookies=cookies,
                action_text="getting catalog",
                method="GET",
            )
        except Exception as e:
            _logger.error("Could not fetch catalog_by_kdp for url %s: %s", url, e)
            continue
        if response_from_amazon:
            # book_count = response_from_amazon.get("totalCount", None)
            books_on_amazon = response_from_amazon.get("products", None)
            cursor_token = response_from_amazon.get("cursorToken", "")
            if books_on_amazon:
                all_books_on_amazon.extend([book for book in books_on_amazon if book not in all_books_on_amazon])
            if books_on_amazon is None or ("cursorToken" in response_from_amazon and cursor_token == ""):
                break
    return all_books_on_amazon
    
def get_catalog_by_amazon(url, headers, cookies, country_code, entity_id):
    all_books_on_amazon = []
    asins = get_asins(entity_id, country_code)

    for asin in asins:
        # no cursor toek in the UK
        payload = {
            "programType": "SP",
            "catalogType": "AMAZON",
            "searchString": asin,
            "pageIndex": "0",
            "pageSize": "50",
            "additionalProductInfo": "ELIGIBILITY",
        }

        try:
            response_from_amazon = do_json_request(
                url=url,
                headers=headers,
                params=payload,
                cookies=cookies,
                action_text="getting catalog",
                method="GET",
            )
        except:
            continue
        if response_from_amazon:
            # book_count = response_from_amazon.get("totalCount", None)
            books_on_amazon = response_from_amazon.get("products", None)
            if books_on_amazon:
                all_books_on_amazon.extend([book for book in books_on_amazon if book not in all_books_on_amazon])
    return all_books_on_amazon

def get_catalog(entity_id: str, country_code: str):
    """Gets all the books in a profile's catalog on Amazon via the products? GET request"""
    domain = DOMAINS.get(country_code)
    if domain is None:
        _logger.error("Domain not found for country code: %s", country_code)
        return None

    profile_info = get_profile_info(entity_id=entity_id, country_code=country_code)
    if profile_info is None:
        _logger.error("Could not fetch profile info for entity: %s in %s", entity_id, country_code)
        return
    csrf_token = profile_info.get("csrfToken")
    client_id = profile_info.get("clientId")
    marketplace_id = profile_info.get("marketplaceId")
    console_id = profile_info.get("consoleId")
    headers = {
        "Amazon-Advertising-API-CSRF-Token": f"{csrf_token}",
        "Amazon-Advertising-API-CSRF-Data": f"{client_id}",
        "Amazon-Advertising-API-ClientId": f"{client_id}",
        "Amazon-Advertising-API-MarketplaceId": f"{marketplace_id}",
        "Amazon-Advertising-API-AdvertiserId": f"{entity_id}",
        "Amazon-Advertising-API-ConsoleId": f"{console_id}",
    }
    cookies = read_cookies()
    cookies_for_country = cookies[country_code]
    url = f"https://advertising.amazon.{domain}/a9g-api/v2/products"
    books_on_amazon = get_catalog_by_kdp(url, headers, cookies_for_country)
    if len(books_on_amazon) == 0:
        books_on_amazon = get_catalog_by_amazon(url, headers, cookies_for_country, country_code, entity_id)
    return books_on_amazon


#############################################################################################
################################### BRAND CAMPAIGNS #########################################
#############################################################################################


@app.task
def sync_brand_campaigns():
    """Downlad the data from Amazon Console via fetch for Brand Campaigns"""
    managed_profiles = _get_managed_profiles()
    if not managed_profiles:
        return
    date_from, date_to = _set_epoch_times(days_from=32, days_to=1)
    for profile in managed_profiles:
        entity_id = profile.entity_id
        country_code = profile.country_code
        csrf_token = _get_csrf_from_page(entity_id=entity_id, country_code=country_code)
        if csrf_token is None:
            continue
        brand_campaigns = _get_brand_campaigns(
            entity_id=profile.entity_id,
            country_code=country_code,
            csrf_token=csrf_token,
            date_from=date_from,
            date_to=date_to,
        )
        if not brand_campaigns:
            continue
        brand_campaign_ids_amazon = []
        for campaign in brand_campaigns:
            brand_campaign_id = campaign.get("id")
            campaign_api_external_id = abs(int(campaign.get("campaignApiExternalId")))
            brand_campaign_ids_amazon.append(campaign_api_external_id)
            campaign_in_db = Campaign.objects.update_or_create(
                brand_campaign_id=brand_campaign_id,
                sponsoring_type="sponsoredBrands",
                defaults={
                    "campaign_id_amazon": campaign_api_external_id,
                    "profile": profile,
                    "serving_status": campaign.get("status"),
                    "campaign_name": campaign.get("name"),
                    "state": campaign.get("state"),
                    "targeting_type": campaign.get("targetingType"),
                    "daily_budget": Decimal(campaign.get("budget").get("millicents")),
                },
            )
            ad_group_id = _get_brand_ad_group_id(
                entity_id=entity_id,
                country_code=country_code,
                brand_campaign_id=brand_campaign_id,
                csrf_token=csrf_token,
            )
            if len(ad_group_id) == 0:
                _logger.error(
                    "Error in getting brand ad group id for campaign: %s on entity: %s",
                    brand_campaign_id,
                    entity_id,
                )
            AdGroup.objects.update_or_create(
                campaign=campaign_in_db[0],
                brand_ad_group_id=ad_group_id,
                defaults={
                    "ad_group_id": campaign_api_external_id,
                    "ad_group_name": campaign.get("name"),
                },
            )
        # if a campaign doesn't exist in the ENABLED objects on Amazon, set it to paused
        existing_brand_campaigns_in_db = (
            Campaign.objects.filter(profile=profile, sponsoring_type="sponsoredBrands")
            .values_list("campaign_id_amazon", flat=True)
            .distinct("campaign_id_amazon")
        )
        for db_campaign_id in existing_brand_campaigns_in_db:
            if db_campaign_id not in brand_campaign_ids_amazon:
                db_campaign = Campaign.objects.get(campaign_id_amazon=db_campaign_id)
                db_campaign.serving_status = "PAUSED"
                db_campaign.save()


def _get_csrf_from_page(entity_id: str, country_code: str):
    """Get CSRF token from page HTML"""
    domain = DOMAINS.get(country_code)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.5",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    cookies = read_cookies()
    url = f"https://advertising.amazon.{domain}/cm/campaigns?entityId={entity_id}"
    session = get_new_retry_session()
    response = session.get(url=url, headers=headers, cookies=cookies[country_code])
    page_text = response.text
    csrf_token_browser = re.search('(?<=csrfToken: ").+?(?=")', page_text)
    try:
        csrf_token_browser_extracted = csrf_token_browser.group()  # type: ignore
    except:
        csrf_token_browser_extracted = None
    return csrf_token_browser_extracted


def _get_brand_campaigns(entity_id: str, country_code: str, csrf_token: str, date_from: int, date_to: int):
    """Gets all the brand campaigns in a profile on Amazon via the products? POST request"""
    domain = DOMAINS.get(country_code)
    #  csrf_token = _get_csrf_from_page(entity_id=entity_id, country_code=country_code)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
        "Accept": "*/*",
        "Accept-Language": "en-GB,en;q=0.5",
        "content-type": "application/json",
        "X-CSRF-token": f"{csrf_token}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    cookies = read_cookies()
    url = f"https://advertising.amazon.{domain}/cm/api/campaigns?entityId={entity_id}&"
    body = {
        "fields": [
            "CAMPAIGN_NAME",
            "CAMPAIGN_ELIGIBILITY_STATUS",
            "CAMPAIGN_SMART_BIDDING_STRATEGY",
            "BID_ADJUSTMENT_PERCENTAGE",
            "CAMPAIGN_STATE",
            "CAMPAIGN_START_DATE",
            "CAMPAIGN_END_DATE",
            "CAMPAIGN_BUDGET",
            "CAMPAIGN_BUDGET_CURRENCY",
            "CAMPAIGN_BUDGET_TYPE",
            "CAMPAIGN_TYPE",
            "PORTFOLIO_NAME",
            "CAMPAIGN_BUDGET_RULE_ID",
            "CAMPAIGN_BUDGET_RULE_NAME",
            "CAMPAIGN_RULE_BASED_BUDGET",
            "CAMPAIGN_EFFECTIVE_BUDGET",
            "KINDLE_UNLIMITED_PAGES_READ",
            "KINDLE_UNLIMITED_ROYALTIES",
            "IMPRESSIONS",
            "CLICKS",
            "SPEND",
            "CTR",
            "CPC",
            "ORDERS",
            "SALES",
            "ACOS",
            "BID_TYPE",
        ],
        "filters": [
            {
                "field": "CAMPAIGN_STATE",
                "not": False,
                "operator": "EXACT",
                "values": ["ENABLED"],
            },
            {
                "field": "CAMPAIGN_PROGRAM_TYPE",
                "not": False,
                "operator": "EXACT",
                "values": ["HSA", "SBV"],
            },
        ],
        "pageOffset": 0,
        "pageSize": 300,
        "period": "CUSTOM",
        "programType": "SP",
        "queries": [],
        "sort": {"field": "SPEND", "order": "DESC"},
        "startDateUTC": f"{date_from}",
        "endDateUTC": f"{date_to}",
        "timeSeriesInterval": "DAY",
        "version": "V2",
    }
    brand_campaigns = do_json_request(
        url=url,
        headers=headers,
        cookies=cookies[country_code],
        body=body,
        action_text="getting brand campaigns",
        method="POST",
    )
    brand_data = None if brand_campaigns is None else brand_campaigns.get("data", None)
    return brand_data


def _get_brand_ad_group_id(entity_id: str, country_code: str, brand_campaign_id: str, csrf_token: str) -> str:
    """Gets ad group primary id to make further requests"""
    domain = DOMAINS.get(country_code)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
        "Accept": "*/*",
        "Accept-Language": "en-GB,en;q=0.5",
        "content-type": "application/json",
        "X-CSRF-token": f"{csrf_token}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Cache-Control": "max-age=0",
    }
    cookies = read_cookies()
    url = f"https://advertising.amazon.{domain}/cm/sb/api/campaigns/{brand_campaign_id}?entityId={entity_id}"
    ad_group_info = do_json_request(
        url=url,
        headers=headers,
        cookies=cookies[country_code],
        action_text="getting brand ad group id",
        method="GET",
    )
    ad_group_id = (
        "" if ad_group_info is None else ad_group_info.get("campaign", None).get("primaryAdGroupId", None)
    )
    return ad_group_id


def _set_epoch_times(days_from: int, days_to: int):
    """Calculates the epoch timestamps for Amazon console requests in ms"""
    today = datetime.today()
    date_from = today - timedelta(days=days_from)
    date_to = today - timedelta(days=days_to)
    date_from = date_from.date()  # type: ignore
    date_to = date_to.date()  # type: ignore
    date_from = datetime.combine(date_from, datetime.min.time())
    date_to = datetime.combine(date_to, datetime.min.time())
    date_from = int(date_from.timestamp() * 1000)  # type: ignore
    date_to = int(date_to.timestamp() * 1000) - 1  # type: ignore
    return date_from, date_to


@app.task
def adjust_brand_bids():
    """Manage brand campaign bids"""
    managed_profiles = Profile.objects.filter(
        managed=True,
        campaigns__sponsoring_type="sponsoredBrands",
        campaigns__managed=True,
    ).distinct("profile_id")
    if not managed_profiles:
        return
    date_from, date_to = _set_epoch_times(days_from=32, days_to=1)
    for profile in managed_profiles:
        entity_id = profile.entity_id
        country_code = profile.country_code
        currency = CURRENCIES.get(country_code)
        csrf_token = _get_csrf_from_page(entity_id=entity_id, country_code=country_code)
        if csrf_token is None:
            continue
        managed_campaigns = (
            Campaign.objects.filter(profile=profile, sponsoring_type="sponsoredBrands", managed=True)
            .exclude(campaign_name__contains="-GP-")
            .prefetch_related("ad_groups")
        )
        if not managed_campaigns:
            continue
        for campaign in managed_campaigns:
            brand_ad_group_id = campaign.ad_groups.first().brand_ad_group_id  # type: ignore
            if not brand_ad_group_id:
                continue
            brand_targets = _get_brand_targets(
                entity_id=entity_id,
                country_code=country_code,
                brand_campaign_id=campaign.brand_campaign_id,
                ad_group_id=brand_ad_group_id,
                csrf_token=csrf_token,
                date_from=date_from,
                date_to=date_to,
            )
            if not brand_targets:
                continue
            match_type = brand_targets[0].get("matchType")
            # this is for bid update endpoint
            target_type = "targets" if match_type == "TARGETING_EXPRESSION" else "keywords"
            brand_target_slices = _process_brand_targets(brand_targets=brand_targets)
            bid_change_body = []
            for brand_target_id, brand_target_datum in brand_target_slices.items():
                slice = brand_target_datum.get("ad_slice")
                val_change, pause = _campaign_adjust(
                    slice=slice,  # type: ignore
                    target_acos=0.4,
                    current_val=brand_target_datum.get("bid"),
                    book_price=15.0,
                )
                if val_change != 0:
                    float_bid = round(float(brand_target_datum.get("bid")) + val_change, 2)  # type: ignore
                    float_bid_str = str(float_bid)
                    if len(float_bid_str[float_bid_str.index(".") + 1 :]):
                        float_bid += 0.01
                    bid = int(float_bid * 100000)
                    single_body = {
                        "bid": {"currencyCode": currency, "millicents": bid},
                        "canonicalId": brand_target_datum.get("canonical_id"),
                        "id": brand_target_id,
                        "programType": "HSA",
                    }
                    bid_change_body.append(single_body)
            if len(bid_change_body) > 0:
                _update_brand_targets(
                    entity_id=entity_id,
                    country_code=country_code,
                    brand_campaign_id=campaign.brand_campaign_id,
                    ad_group_id=brand_ad_group_id,
                    body=bid_change_body,
                    target_type=target_type,
                )


def _process_brand_targets(brand_targets: List[Dict]) -> Dict[str, Dict[str, AdSlice]]:
    """Process brand targets response from Amazon into AdSlices for processing using the logic function Campaign Adjust"""
    brand_target_slices: Dict[str, Dict] = {}  # str will be the target ID and AdSlice the data
    for data in brand_targets:
        target_id = data.get("id", None)
        bid = data.get("bid").get("millicents") / 100000  # type: ignore
        canonical_id = data.get("canonicalId")
        sales = data.get("sales").get("millicents") / 100000  # type: ignore
        spend = data.get("spend").get("millicents") / 100000  # type: ignore
        kenp_royalties = data.get("kindleUnlimitedRoyalties").get("millicents") / 100000  # type: ignore
        impressions = data.get("impressions", 0)
        clicks = data.get("clicks", 0)
        orders = data.get("orders", 0)
        brand_target_slices[target_id] = {  # type: ignore
            "bid": bid,
            "canonical_id": canonical_id,
            "ad_slice": AdSlice(
                sales=sales,
                spend=spend,
                kenp_royalties=kenp_royalties,
                impressions=impressions,
                clicks=clicks,
                orders=orders,
            ),
        }
    return brand_target_slices


def _process_brand_search_terms(
    brand_search_terms: List[Dict], search_term_identifier: str
) -> Dict[str, AdSlice]:
    """Process brand serach terms response from Amazon into AdSlices for processing using the logic function Campaign Adjust"""
    brand_search_term_slices: Dict[str, AdSlice] = {}  # str will be the target ID and AdSlice the data
    for data in brand_search_terms:
        keyword_text = data.get("settings").get(search_term_identifier, None)  # type: ignore
        performance_data = data.get("intervalData").get("SUMMARY", None)[0]  # type: ignore
        for k, v in performance_data.items():
            if v is not None:
                if "." in v:
                    performance_data[k] = round(float(v), 2)
                else:
                    performance_data[k] = int(v)
        sales = performance_data.get("SALES") / 100000  # type: ignore
        spend = performance_data.get("SPEND") / 100000  # type: ignore
        impressions = performance_data.get("IMPRESSIONS", 0)
        clicks = performance_data.get("CLICKS", 0)
        orders = performance_data.get("ORDERS", 0)
        brand_search_term_slices[keyword_text] = AdSlice(
            sales=sales,
            spend=spend,
            kenp_royalties=0,
            impressions=impressions,
            clicks=clicks,
            orders=orders
            # type: ignore
        )
    return brand_search_term_slices


def _get_brand_targets(
    entity_id: str,
    country_code: str,
    brand_campaign_id: str,
    ad_group_id: str,
    csrf_token: str,
    date_from: int,
    date_to: int,
):
    """Gets all the brand targets in ad group in brand campaign in a profile on Amazon via the products? POST request"""
    domain = DOMAINS.get(country_code)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
        "Accept": "*/*",
        "Accept-Language": "en-GB,en;q=0.5",
        "content-type": "application/json",
        "X-CSRF-token": f"{csrf_token}",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    cookies = read_cookies()
    url = f"https://advertising.amazon.{domain}/cm/sb/api/campaigns/{brand_campaign_id}/adgroups/{ad_group_id}/keywords?entityId={entity_id}&"
    body = {
        "startDateUTC": f"{date_from}",
        "endDateUTC": f"{date_to}",
        "fields": [
            "KEYWORD_STATE",
            "KEYWORD",
            "KEYWORD_MATCH_TYPE",
            "KEYWORD_ELIGIBILITY_STATUS",
            "TARGETING",
            "IMPRESSIONS",
            "CLICKS",
            "SPEND",
            "CTR",
            "CPC",
            "ORDERS",
            "SALES",
            "ACOS",
            "DETAIL_PAGE_VIEWS",
            "UNITS_SOLD",
            "TOP_OF_SEARCH_KW_IMPRESSION_SHARE",
        ],
        "filters": [
            {
                "field": "KEYWORD_STATE",
                "not": False,
                "operator": "EXACT",
                "values": ["ENABLED"],
            }
        ],
        "pageOffset": 0,
        "pageSize": 300,
        "period": "CUSTOM",
        "programType": "SP",
        "queries": [],
        "sort": {"field": "SPEND", "order": "DESC"},
        "timeSeriesInterval": "DAY",
        "version": "V2",
    }
    brand_campaign_target_data = do_json_request(
        url=url,
        headers=headers,
        cookies=cookies[country_code],
        body=body,
        action_text="getting brand targets",
        method="POST",
    )
    extracted_data = (
        None if brand_campaign_target_data is None else brand_campaign_target_data.get("data", None)
    )
    return extracted_data


def _update_brand_targets(
    entity_id: str,
    country_code: str,
    brand_campaign_id: str,
    ad_group_id: str,
    body: List[Dict],
    target_type: str,
):
    """Update bids on brand campaigns via patch request"""
    domain = DOMAINS.get(country_code)
    profile_info = get_profile_info(entity_id=entity_id, country_code=country_code)
    if profile_info is None:
        _logger.error("Could not fetch profile info for entity: %s in %s", entity_id, country_code)
        return
    csrf_token = profile_info.get("csrfToken")
    client_id = profile_info.get("clientId")
    marketplace_id = profile_info.get("marketplaceId")
    headers = {
        "Amazon-Advertising-API-CSRF-Token": f"{csrf_token}",
        "Amazon-Advertising-API-CSRF-Data": f"{client_id}",
        "Amazon-Advertising-API-ClientId": f"{client_id}",
        "Amazon-Advertising-API-MarketplaceId": f"{marketplace_id}",
        "Amazon-Advertising-API-AdvertiserId": f"{entity_id}",
    }
    cookies = read_cookies()
    url = f"https://advertising.amazon.{domain}/a9g-api-gateway/cm/sb/api/campaigns/{brand_campaign_id}/adgroups/{ad_group_id}/{target_type}?entityId={entity_id}"
    response = requests.patch(url=url, headers=headers, cookies=cookies[country_code], json=body)
    response = do_json_request(
        url=url,
        headers=headers,
        cookies=cookies[country_code],
        body=body,
        action_text="updating brand targets",
        method="PATCH",
    )

    # Example of the body for updating brand targets
    # [
    # 	{
    # 		"bid": {
    # 			"currencyCode": "USD",
    # 			"millicents": 144000
    # 		},
    # 		"canonicalId": "144278778050828926",
    # 		"id": "CH485f00f02b5704090c32867213a15afc",
    # 		"programType": "HSA"
    # 	}
    # ]


def _get_brand_search_terms(
    entity_id: str,
    country_code: str,
    brand_campaign_id: str,
    date_from: str,
    date_to: str,
) -> List[Dict]:
    """Get all brand campaign search terms info"""
    domain = DOMAINS.get(country_code)
    profile_info = get_profile_info(entity_id=entity_id, country_code=country_code)
    if profile_info is None:
        _logger.error("Could not fetch profile info for entity: %s in %s", entity_id, country_code)
        return []
    csrf_token = profile_info.get("csrfToken")
    client_id = profile_info.get("clientId")
    marketplace_id = profile_info.get("marketplaceId")
    headers = {
        "Amazon-Advertising-API-CSRF-Token": f"{csrf_token}",
        "Amazon-Advertising-API-CSRF-Data": f"{client_id}",
        "Amazon-Advertising-API-ClientId": f"{client_id}",
        "Amazon-Advertising-API-MarketplaceId": f"{marketplace_id}",
        "Amazon-Advertising-API-AdvertiserId": f"{entity_id}",
    }
    cookies = read_cookies()
    body = {
        "campaignIdFilter": f"{brand_campaign_id}",
        "startDate": f"{date_from}",
        "endDate": f"{date_to}",
        "pageSize": 300,
        "programAndAdProductTypeList": [{"programType": "SPONSORED_BRANDS"}],
        "selectColumns": [
            "CUSTOMER_SEARCH_TERM",
            "TARGETINGCLAUSE_MATCH_TYPE",
            "TARGETINGCLAUSE",
            "IMPRESSIONS",
            "CLICKS",
            "CTR",
            "SPEND",
            "CPC",
            "ORDERS",
            "SALES",
            "ACOS",
            "ROAS",
            "CONVERSION_RATE",
        ],
        "sortColumn": "SPEND",
        "sortOrder": "DESCENDING",
        "summaryIntervalGrains": ["SUMMARY"],
    }
    url = f"https://advertising.amazon.{domain}/a9g-api/preview/generatePerformanceReports/online/targetingClauses/searchTerms"
    brand_search_terms_json = do_json_request(
        url=url,
        headers=headers,
        cookies=cookies[country_code],
        body=body,
        action_text="getting brand search terms",
        method="POST",
    )
    extracted_data = [] if brand_search_terms_json is None else brand_search_terms_json.get("adEntities", [])
    return extracted_data


def _get_brand_negatives(
    entity_id: str,
    country_code: str,
    brand_campaign_id: str,
    ad_group_id: str,
    target_type: str,
):
    """Gets existing brand negatives"""
    domain = DOMAINS.get(country_code)
    profile_info = get_profile_info(entity_id=entity_id, country_code=country_code)
    if profile_info is None:
        _logger.error("Could not fetch profile info for entity: %s in %s", entity_id, country_code)
        return []
    csrf_token = profile_info.get("csrfToken")
    client_id = profile_info.get("clientId")
    marketplace_id = profile_info.get("marketplaceId")
    headers = {
        "Amazon-Advertising-API-CSRF-Token": f"{csrf_token}",
        "Amazon-Advertising-API-CSRF-Data": f"{client_id}",
        "Amazon-Advertising-API-ClientId": f"{client_id}",
        "Amazon-Advertising-API-MarketplaceId": f"{marketplace_id}",
        "Amazon-Advertising-API-AdvertiserId": f"{entity_id}",
    }
    cookies = read_cookies()
    body = {
        "adGroupIdFilters": [f"{ad_group_id}"],
        "campaignIdFilters": [f"{brand_campaign_id}"],
        "pageNumber": 1,
        "pageSize": 300,
        "programType": "SB",
        "resourceStateFilters": ["ENABLED", "PENDING"],
        "textSortOrder": "ASC",
    }
    url = f"https://advertising.amazon.{domain}/a9g-api-gateway/cm/sb/api/campaigns/{brand_campaign_id}/adgroups/{ad_group_id}/negative-{target_type}"
    brand_negatives = do_json_request(
        url=url,
        headers=headers,
        cookies=cookies[country_code],
        body=body,
        action_text="getting brand negatives",
        method="POST",
    )
    extracted_data = None if brand_negatives is None else brand_negatives.get("pageElements", None)
    if extracted_data:
        negative_ident = "keywordText" if target_type == "keywords" else "displayValue"
        negatives_list = []
        for datum in extracted_data:
            negatives_list.append(datum[negative_ident])
        return negatives_list
    return []


def _add_negatives_brand_campaign(
    entity_id: str,
    country_code: str,
    brand_campaign_id: str,
    ad_group_id: str,
    body: List[Dict],
    target_type: str,
):
    """Adds negative exact keywords and ASINs to brand campaigns"""
    domain = DOMAINS.get(country_code)
    profile_info = get_profile_info(entity_id=entity_id, country_code=country_code)
    if profile_info is None:
        _logger.error("Could not fetch profile info for entity: %s in %s", entity_id, country_code)
        return
    csrf_token = profile_info.get("csrfToken")
    client_id = profile_info.get("clientId")
    marketplace_id = profile_info.get("marketplaceId")
    headers = {
        "Amazon-Advertising-API-CSRF-Token": f"{csrf_token}",
        "Amazon-Advertising-API-CSRF-Data": f"{client_id}",
        "Amazon-Advertising-API-ClientId": f"{client_id}",
        "Amazon-Advertising-API-MarketplaceId": f"{marketplace_id}",
        "Amazon-Advertising-API-AdvertiserId": f"{entity_id}",
    }
    cookies = read_cookies()
    url = f"https://advertising.amazon.{domain}/a9g-api-gateway/cm/sb/api/campaigns/{brand_campaign_id}/adgroups/{ad_group_id}/negative-{target_type}"
    response_body = do_json_request(
        url=url,
        headers=headers,
        cookies=cookies[country_code],
        body=body,
        action_text="adding negatives to brand campaign",
        method="PUT",
    )
    created_keywords = [] if response_body is None else response_body.get("createdKeywords", [])
    return len(created_keywords)


# Example of the body for adding negatives

# [
# 	{
# 		"keyword": "asin=\"1672148553\"",   <-------- Notive the backslashes so they'll be doubled up
# 		"matchType": "NEGATIVE_TARGETING_EXPRESSION"
# 	}
# ]

# [
# 	{
# 		"keyword": "atomic habits",
# 		"matchType": "NEGATIVE_EXACT"
# 	}
# ]


@app.task
def add_brand_negative_exacts():
    """Add negative exact products and keywords to brand campaign"""
    managed_profiles = Profile.objects.filter(
        managed=True,
        campaigns__sponsoring_type="sponsoredBrands",
        campaigns__managed=True,
    ).distinct("profile_id")
    if not managed_profiles:
        return
    today = datetime.today()
    date_from = today - timedelta(days=32)
    date_to = today - timedelta(days=DEFAULT_DATA_ACCURACY_CUTOFF_DAYS)
    date_from = date_from.strftime("%Y-%m-%d")
    date_to = date_to.strftime("%Y-%m-%d")
    for profile in managed_profiles:
        entity_id = profile.entity_id
        country_code = profile.country_code
        managed_campaigns = Campaign.objects.filter(
            profile=profile, sponsoring_type="sponsoredBrands", managed=True
        ).prefetch_related("ad_groups")
        if not managed_campaigns:
            continue
        for campaign in managed_campaigns:
            positives: List[str] = []
            negatives: List[str] = []
            brand_ad_group_id = campaign.ad_groups.first().brand_ad_group_id  # type: ignore
            if not brand_ad_group_id:
                continue
            brand_search_terms = _get_brand_search_terms(
                entity_id=entity_id,
                country_code=country_code,
                brand_campaign_id=campaign.brand_campaign_id,
                date_from=date_from,
                date_to=date_to,
            )
            if len(brand_search_terms) == 0:
                continue
            match_type = brand_search_terms[0].get("settings").get("TARGETINGCLAUSE_MATCH_TYPE")  # type: ignore
            # this is for bid update endpoint

            target_type = "keywords"
            negative_match_type = "NEGATIVE_EXACT"
            search_term_identifier = "CUSTOMER_SEARCH_TERM"
            if match_type == "TARGETING_EXPRESSION":
                target_type = "targets"
                negative_match_type = "NEGATIVE_TARGETING_EXPRESSION"
                search_term_identifier = "TARGETINGCLAUSE"

            brand_target_slices = _process_brand_search_terms(
                brand_search_terms=brand_search_terms,
                search_term_identifier=search_term_identifier,
            )

            existing_brand_negatives = _get_brand_negatives(
                entity_id=entity_id,
                country_code=country_code,
                brand_campaign_id=campaign.brand_campaign_id,
                ad_group_id=brand_ad_group_id,
                target_type=target_type,
            )

            new_negatives_body = []
            for keyword_text, search_term_ad_slice in brand_target_slices.items():
                if keyword_text in existing_brand_negatives:
                    continue
                positives, negatives = _process_search_term(
                    price=10.0,
                    be_acos=0.4,
                    positives=positives,
                    negatives=negatives,
                    current_keyword=keyword_text,
                    current_query=search_term_ad_slice,
                )
            if len(negatives) > 0:
                for negative in negatives:
                    single_body = {
                        "keyword": negative,
                        "matchType": negative_match_type,
                    }
                    new_negatives_body.append(single_body)
            if len(new_negatives_body) > 0:
                num_negatives_added = _add_negatives_brand_campaign(
                    entity_id=entity_id,
                    country_code=country_code,
                    brand_campaign_id=campaign.brand_campaign_id,
                    ad_group_id=brand_ad_group_id,
                    body=new_negatives_body,
                    target_type=target_type,
                )
                if num_negatives_added is not None:
                    _logger.info(
                        "Added %s SB negatives on profile: %s [%s], campaign: %s",
                        num_negatives_added,
                        profile.nickname,
                        country_code,
                        campaign.campaign_name,
                    )
                else:
                    _logger.info(
                        "Error adding SB negatives on profile: %s [%s], campaign: %s",
                        profile.nickname,
                        country_code,
                        campaign.campaign_name,
                    )


def get_bsrs_info(asins: List[str], country_code: str) -> List[NewRelease]:
    """Gets the BSRs and info of books using Seller Central requests"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
        "Accept": "*/*",
        "Accept-Language": "en-GB,en;q=0.5",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    # cookies_ca = {
    #     "__Host-mselc": "H4sIAAAAAAAA/6tWSs5MUbJSSsytyjPUS0xOzi/NK9HLT85M0XM0dvF0dwsNs3APcDKKUtJRykVSmZtalJyRCFKKRV02ssICkBIj19BAw/AQd+cQJ3cjpVoAiBqrPXYAAAA=",
    #     "at-acbca": "Atza|IwEBIF0jlxMHTCqlfPNYXzzNZ5dPQguDAqvW_m42F_jwAnLbMMOUgI0qW9FY514NQOsLMsM-ZWOU2S3B3-J8-pGrWaTYmXL-rU8fx9FuaMUzz1hJqrms277sqPbPlaCp14hN6ckJBBUhQRJTVOzfHr2ZDK2Nps58j1yThSC5DTT0CE0YGfGIEyEFf7BvJeBxgmfaKA4QUJ4GqMQS86rgt2cXBygIUyUDikgZL3u38ikJj6C6Tqh_BgUaiuiyHnKWTD57ZdYzUBWc4CUiJjl7v-3YWQNnGWoT5FlfglgCWTm5tG7Mvw",
    #     "ubid-acbca": "131-0651022-9501758",
    # }
    # cookies_us = {
    #     "__Host-mselc": "H4sIAAAAAAAA/6tWSs5MUbJSSsytyjPUS0xOzi/NK9HLT85M0XM0dvF0dwsNs3APcDKKUtJRykVSmZtalJyRCFKKRV02ssICkJKQsAAXb0/vCAMX1yClWgDFkissdQAAAA==",
    #     "at-main": "Atza|IwEBIMbcur_7eYo70nKnY4WsBzIybNgDi5_HLWieLmyPzz6r-PlrrziJlOikcw2m5J2kA9CDxV_nuOnLjswv-FS5IBotwPTOivTQCpruGNjKHENZpXCN6gWzxQrkN6PyeQOlr4W8SvTx4MQ3wTvLaBXIEwvH98GNqt-xDZdzxL70loTo-9gzYVGdKHDMOerSOElg_LzYASqjSQK1GG0uLzBXCTmSUlaV-denNePxChRa52IBcg",
    #     "ubid-main": "132-8094640-4247560",
    # }
    # cookies = {
    #     "__Host-mselc": "H4sIAAAAAAAA/6tWSs5MUbJSSsytyjPUS0xOzi/NK9HLT85M0XM0dvF0dwsNs3APcDKKUtJRykVSmZtalJyRCFKq52hs6hzo7Rfmb+QaauwMUpeNrLAApMTQzcLY3cLZyDHI3zxAqRYAW5Hh0XYAAAA=",
    #     "at-acbuk": "Atza|IwEBIHsWknj4bg51pk1JJbJ2bFGfz7ogbmDNKDpyHr4YtA1nJkWmPaINgFLBfr9KQoDG-tws6PsjP2YpjcEhs-EPRvoURmZFjdT7pDCL1ro18cIC0DhCxgkFr_bU2ECnb2maXA-fckpSlYYVgG5g0THS_eH6kUwipUpeDwviaf8Wz1vJKcN7cag_R9DwZBOflwxnQnhO3r0sVcGWkFTkf0KCP7I_hVe9-iMIIm46keri0evA3w",
    #     "ubid-acbuk": "260-5675796-0844422",
    # }
    cookies = read_cookies(seller=True)
    domain = DOMAINS.get(country_code)
    new_release_info = []
    for asin in asins:
        url = f"https://sellercentral.amazon.{domain}/productsearch/search?query={asin}&page=1"
        response_from_amazon = do_json_request(
            url=url,
            headers=headers,
            cookies=cookies[country_code],
            action_text="getting BSR info",
            method="GET",
        )
        if response_from_amazon:
            bsr = response_from_amazon.get("products")[0].get("salesRank", 0)
            image_url = response_from_amazon.get("products")[0].get("imageUrl", "")
            title = response_from_amazon.get("products")[0].get("title", "")
            title = title[:249] if len(title) > 249 else title
            bsr_int = int(bsr) if len(bsr) > 0 else 0
            new_release_info.append(
                NewRelease(
                    asin=asin,
                    bsr=bsr_int,
                    image_url=image_url,
                    title=title,
                    country_code=country_code,
                )
            )
    return new_release_info


@app.task
def recalculate_acos(profile_id: Optional[int] = None, force: Optional[bool] = False):
    """Recalculates break even ACOS"""
    book_filter = Book.objects.filter(in_catalog=True, pages__gt=0, price__gt=0).exclude(format="Kindle")

    books_per_marketplace = {
        marketplace: book_filter.filter(profile__country_code=marketplace)
        for marketplace in ["US", "CA", "UK"]
        if book_filter.filter(profile__country_code=marketplace).exists()
    }
    if len(books_per_marketplace) == 0:
        return
    for marketplace, books in books_per_marketplace.items():
        # catalog_api = CatalogAPI(marketplace=Marketplaces[marketplace.label])  # type: ignore
        if marketplace == "UK":
            marketplace = "GB"
        for book in books:
            be_acos = book_info._get_be_acos(
                book=book, book_length=book.pages, country=book.profile.country_code
            )
            book.be_acos = Decimal(be_acos)
            book.save()


#################################################################


def scrape_new_releases_page(keyword: str, region: Optional[str], page: int):
    """Gets and scrapes 1 page of new releases in the last 30 days from Scrape Stack"""
    number_of_pages = 0
    if region == "GB":
        url = f"https://www.amazon.co.uk/s?k={keyword}&rh=n:266239,p_n_binding_browse-bin:492564011,p_n_publication_date:182241031&page={page}"
    elif region == "CA":
        url = f"https://www.amazon.ca/s?k={keyword}&rh=n:916520,p_n_binding_browse-bin:2366374011,p_n_date:12035756011&page={page}"
    else:
        url = f"https://www.amazon.com/s?k={keyword}&rh=n:283155,p_n_publication_date:1250226011,p_n_feature_browse-bin:2656022011&page={page}"

    response = get_html_via_proxy(url=url)
    if response is None:
        return None, None
    
    doc = BeautifulSoup(response.text, "html.parser")
    if page == 1:
        # get the number of results
        breadcrumb = doc.find("div", attrs={"class": re.compile(".breadcrumb.")})
        text = breadcrumb.text.rstrip("\n").strip("\n")  # type: ignore
        prog = re.compile("\\d{0,4},?\\d{0,4}(?=\\sresults)")
        total_results_text = prog.search(text)
        if total_results_text is not None:
            total_results = int(total_results_text[0].replace(",", ""))
            number_of_pages = math.ceil(total_results / 20)
        else:
            total_results = 0
            _logger.info(
                "Could not get total results for keyword: %s in region: %s",
                keyword,
                region,
            )
        if total_results < MIN_RESULTS_PER_AMAZON_SEARCH_PAGE:
            return None, None
    # get the ASINs
    divs = doc.find_all("div")
    asins = []
    for div in divs:
        if div.has_attr("data-asin"):
            asin = div["data-asin"]
            if len(asin) == 10:
                asins.append(asin)
    # find the number of pages
    # navigation = doc.find_all("span", attrs={"class": re.compile("^s-pagination-item.*")})
    # number_of_pages = int(navigation[-1].text) if len(navigation) != 0 else 1
    return asins, number_of_pages


def get_new_releases(keyword: str, region: Optional[str]) -> List[str]:
    """Gets up to 10 pages of new release ASINs off Amazon"""
    page_asins, pages = scrape_new_releases_page(keyword=keyword, region=region, page=1)
    if pages is None or page_asins is None:
        return []
    if pages == 1 and len(page_asins) > 0:
        return page_asins
    max_pages = 10 if pages > 10 else pages
    _logger.info("Max pages found for keyword '%s': %s", keyword, max_pages)
    all_asins = []
    all_asins.extend(page_asins)
    for page in range(2, max_pages):
        _logger.info("Searching for new releases on page: %s", str(page))
        page_asins, pages = scrape_new_releases_page(keyword=keyword, region=region, page=page)
        if page_asins is None:
            continue
        all_asins.extend(page_asins)
    if len(all_asins) > 0:
        _logger.info("Found %s ASINs", len(all_asins))
    return all_asins


def find_new_asins_for_releavancy_check(keywords: List[str], country_code: str) -> List[NewRelease]:
    """Finds newly released profitable books to advertise on"""
    region = "GB" if country_code == "UK" else country_code
    all_new_releases = []
    for keyword in keywords:
        # new_releases_asins_for_keyword = book_info.get_new_releases(keyword=keyword, region=region)
        new_releases_asins_for_keyword = get_new_releases(keyword=keyword, region=region)
        if len(new_releases_asins_for_keyword) == 0:
            continue
        all_new_releases.extend(new_releases_asins_for_keyword)
    all_new_releases_asins = list(dict.fromkeys(all_new_releases))
    profitable_new_releases = []
    new_releases_info = get_bsrs_info(asins=all_new_releases_asins, country_code=country_code)
    for new_release in new_releases_info:
        if new_release.bsr != 0 and new_release.bsr < MAX_PROFITABLE_BSR:
            profitable_new_releases.append(new_release)
    # new_releases_asins = profitable_new_releases[:149]  # this will create a max of 5 campaigns
    _logger.info(
        "%s profitable new release found for the provided keywords",
        len(profitable_new_releases),
    )
    return profitable_new_releases


def get_profitable_target_books_to_check_relevance():
    """Find profitable new release ASINs"""
    nickname = "Aaminah"
    country_code = "US"
    asin = "B08WZCVC1D"
    keywords = [
        # "financial planning for college graduates",
        # "money for young adults",
    ]

    profile: Profile = Profile.objects.get(nickname=nickname, country_code=country_code)
    book = Book.objects.get(profile=profile, asin=asin)
    new_profitable_asins = find_new_asins_for_releavancy_check(keywords=keywords, country_code=country_code)
    if len(new_profitable_asins) == 0:
        return
    new_releases_in_country = NewRelease.objects.filter(country_code=country_code)
    new_profitable_asins_to_add = []
    for new_release in new_profitable_asins:
        if new_release not in new_releases_in_country:
            new_profitable_asins_to_add.append(new_release)
    NewRelease.objects.bulk_create(new_profitable_asins_to_add, ignore_conflicts=True)
    # get asins already being targeted
    targeted_asins = (
        Target.objects.filter(
            campaign__asins__contains=[book.asin],
            serving_status__in=TARGETS_VALID_STATUSES,
            keyword_type="Positive",
            state=SpState.ENABLED.value,
        )
        .values_list("resolved_expression_text", flat=True)
        .distinct("resolved_expression_text")
    )
    # create a list of entries for the NewReleases and Relevancy models
    new_relevance_list = []
    for new_asin in new_profitable_asins_to_add:
        if new_asin.asin not in targeted_asins:
            new_release = NewRelease.objects.filter(
                asin=new_asin.asin, country_code=new_asin.country_code
            ).first()
            new_relevance_list.append(Relevance(book=book, new_release=new_release))
    if len(new_relevance_list) > 0:
        Relevance.objects.bulk_create(new_relevance_list, ignore_conflicts=True)
    _logger.info(
        "%s new release ASINs added for %s on %s [%s]",
        len(new_relevance_list),
        book,
        profile.nickname,
        profile.country_code,
    )


def target_checked_new_releases():
    """Creates campaigns for checked new releases"""
    # add any ASINs to existing scale campaigns, if there are new_asins_to_add left over, then create new campaigns
    from apps.ads_api.campaigns.product.product_comp_campaign import ProductCompCampaign

    relevant_new_releases = Relevance.objects.filter(relevant=True, targeting=False)
    if not relevant_new_releases.exists():
        return
    new_releases_per_book: Dict[Book, List[str]] = {}
    for relevant in relevant_new_releases:
        if relevant.book in new_releases_per_book:
            new_releases_list = new_releases_per_book[relevant.book]
            new_releases_list.append(relevant.new_release.asin)
            new_releases_per_book[relevant.book] = new_releases_list
        else:
            new_releases_per_book[relevant.book] = [relevant.new_release.asin]
    for book, new_asins_to_add in new_releases_per_book.items():
        # new_asins_to_add = new_releases_per_book[book]
        # for book_entry in new_releases:
        #     new_asins_to_add.append(book_entry)
        all_targets_array = []
        if len(new_asins_to_add) > 0:
            # get scale campaign
            # Get assigned Exact-Scale or Product-Comp campaign
            # see if there is a scale campaign and offload some keywords to that scale campaign, if there's room
            scale_campaign = getattr(book, "campaign_scale_asin")
            if scale_campaign:
                # Get singular ad group of that campaign
                ad_group_in_scale = scale_campaign.ad_groups.first()
                if ad_group_in_scale:
                    # Get number of enabled targets
                    positive_targets = Target.objects.filter(
                        ad_group_id=ad_group_in_scale.ad_group_id,
                        keyword_type="Positive",
                        state=SpState.ENABLED.value,
                    )
                    targets_room = CAMPAIGN_MAX_TARGETS_MAP["Product-Comp"] - positive_targets.count()
                    if targets_room >= 1:
                        # only add the number of keywords there's space for, the others will be added later
                        for asin in new_asins_to_add[:targets_room]:
                            request_body = BodyDict(
                                endpoint=SpEndpoint.TARGETS,
                                campaign_id=scale_campaign.campaign_id_amazon,
                                ad_group_id=ad_group_in_scale.ad_group_id,
                                target_text=asin,
                            )
                            all_targets_array.append(request_body.value)
                        new_asins_to_add = new_asins_to_add[targets_room:]
        if len(new_asins_to_add) > 0:
            campaign = ProductCompCampaign(book=book, text_targets=new_asins_to_add)
            campaign.create()

def get_product_own_campaigns() -> QuerySet[Campaign]:
    campaigns = Campaign.objects.filter(
        campaign_purpose=CampaignPurpose.Product_Own,
    )
    return campaigns
def get_asins_from_product_own_campaign(campaign: Campaign)->list[str]:
    asins = ProductAd.objects.filter(
        campaign=campaign
    ).values_list('asin', flat=True)
    return asins
def get_default_book_for_product_own_campaign(asins: list[str]) -> Book:
    return Book.objects.filter(
        asin__in=asins,
    ).first()
def get_new_books_for_product_own_campaign(campaign: Campaign, book: Book, asins: list[str]) -> QuerySet[Book]:
    books = Book.objects.filter(
        profile=campaign.profile,
        author=book.author,
        eligible=True,
    ).exclude(asin__in=asins)
    return books
def update_product_own_campaigns_with_new_books():
    campaigns=get_product_own_campaigns()
    for campaign in campaigns:
        try:
            asins=get_asins_from_product_own_campaign(campaign)
            if not asins:
                continue
            default_book = get_default_book_for_product_own_campaign(asins)
            if not default_book or not default_book.author:
                continue
            new_books = get_new_books_for_product_own_campaign(campaign, default_book, asins)
            if not new_books:
                continue

            update_campaign_with_new_books(campaign, default_book, new_books)
        except Exception as e:
            _logger.error(f"Failed updating Product-Own campaign {campaign.campaign_name}. Error: {str(e)}")

def update_campaign_with_new_books(campaign: Campaign, default_book: Book, new_books: QuerySet[Book]):
    _logger.info("Updating Product-Own campaign")
    new_asins = new_books.values_list('asin', flat=True)
    product_own_campaign = ProductOwnCampaign(book=default_book, text_targets=new_asins, default_bid=DEFAULT_MAX_BID)
    product_own_campaign.update(campaign, new_books)

@app.task
def mark_targeted_relevancy():
    """Marks processed relevancy entries as "Targeting" if they're found in Amazon campaigns"""
    targets_unique_books = Relevance.objects.filter(targeting=False, checked=True).distinct("book")
    if not targets_unique_books.exists():
        return
    unique_books = []
    for relevant in targets_unique_books:
        unique_books.append(relevant.book)
    rel_entires_to_update = []
    for book in unique_books:
        existing_targets = (
            Target.objects.filter(
                campaign__profile=book.profile,
                campaign__asins__contains=[book.asin],
                serving_status__in=TARGETS_VALID_STATUSES,
                keyword_type="Positive",
                state=SpState.ENABLED.value,
            )
            .values_list("resolved_expression_text", flat=True)
            .distinct("resolved_expression_text")
        )
        targets_to_check = Relevance.objects.filter(targeting=False, checked=True, book=book)
        relevant: Relevance
        for relevant in targets_to_check:
            if relevant.new_release.asin in existing_targets:
                relevant.targeting = True
                rel_entires_to_update.append(relevant)
    if len(rel_entires_to_update) > 0:
        Relevance.objects.bulk_update(rel_entires_to_update, ["targeting"], batch_size=1000)


@app.task
def clean_up_old_reports():
    """Deletes reports older than 65 days"""
    today = datetime.today()
    date = today - timedelta(days=65)
    old_reports = Report.objects.filter(report_for_date__lt=date)
    old_reports.delete()


def add_ASIN_campaign_name(profiles: Optional[QuerySet[Profile]] = None):
    """Adds the ASIN to the campaign name for easy filtering"""
    profiles = Profile.objects.filter(managed=True) if profiles is None else profiles
    for profile in profiles:
        managed_campaigns = Campaign.objects.filter(
            profile=profile,
            # managed=True,
            # state="enabled",
            sponsoring_type="sponsoredProducts",
        )
        campaigns_to_rename = []
        for campaign in managed_campaigns:
            if len(campaign.asins) == 0:
                continue
            if campaign.asins[0] not in campaign.campaign_name:
                new_campaign_name = campaign.campaign_name + "-" + campaign.asins[0]
                campaigns_to_rename.append(
                    CampaignEntity(external_id=campaign.campaign_id_amazon, name=new_campaign_name).dict(
                        exclude_none=True, by_alias=True
                    )
                )
        _logger.info("Campaigns renamed: %s", len(campaigns_to_rename))
        _logger.info("Campaigns renamed: %s", campaigns_to_rename)
        if len(campaigns_to_rename) > 0:
            campaign_adapter = CampaignAdapter(profile)
            successfully_updated, errors = campaign_adapter.batch_update(campaigns_to_rename)
            if errors:
                _logger.error(
                    "Some compaigns were not updated. Updated [%s], errors [%s]",
                    successfully_updated,
                    errors,
                )
                raise BaseAmazonAdsException(
                    "Some campaigns were not updated. To see additional information, please "
                    f"refer to the logs. Time - {datetime.now()}"
                )


def get_html_via_proxy(url: str, proxy_location: Optional[str] = None):
    """Creates a retry session and tries to get data from URL"""
    for try_count in range(3):
        payload = {
            "api_key": SCRAPE_OPS_KEY,
            "url": url,
            "country": proxy_location
            if proxy_location
            else random.choice(SCRAPE_OPS_PROXY_LOCATIONS),
            "residential": "true",
        }
        headers = random.choice(HEADERS_LIST)
        try:
            session = get_new_retry_session()
            response = session.get(SCRAPE_OPS_BASE_URL, params=payload, headers=headers)
            response.raise_for_status()
        except RequestException as err:
            _logger.error("Error connecting via ScrapeOps: %s", err)
            continue
        if '"success":false' in response.text and "@apilayer.com" in response.text:
            # print("Error requesting via ScrapeOps")
            continue
        if (
            "To discuss automated access to Amazon data" in response.text
            or "Sorry, we just need to make sure you're not a robot." in response.text
            or "econnrefused" in response.text
        ):
            # print(f"Amazon isn't giving up their data for URL: {url}")
            continue
        try:
            if response.json().get("success") is False:
                _logger.error("Unsuccessful request via ScrapeOps: %s", response.text)
                continue
            # got the data so move out of the requests loop
            break
        except requests.exceptions.JSONDecodeError:
            break
    if try_count == 2:
        # move onto the next book
        return None
    else:
        return response


def extract_asins_from_html(html_text: str) -> List[str]:
    """Parses Amazon search page HTML, returns SB, SP, organic ASINs"""
    html = BeautifulSoup(html_text, "html.parser")
    # get SP ASINs - sponsored and organic
    products_elements = html.select('div[class*="s-result-item"]')
    sp_asins = []
    organic_asins = []
    for entry in products_elements:
        asin = entry.get("data-asin")
        if asin is None:
            continue
        if len(asin) > 0:
            if "AdHolder" in entry.get("class"):
                sp_asins.append(asin)
            else:
                organic_asins.append(asin)
    # get SB ASINs
    products_elements = html.select("div[data-avar]")
    sb_asins = [entry.get("data-asin") for entry in products_elements if len(entry.get("data-asin")) > 0]
    return sb_asins, sp_asins, organic_asins  # type: ignore


@app.task
def rename_campaigns_standard(profile_ids: Optional[list[int]] = None):
    """Analyses campaign structure to rename campaigns to AdsDroid standard naming convention"""
    if profile_ids:
        profiles = Profile.objects.filter(id__in=profile_ids)
    else:
        profiles = Profile.objects.filter(managed=True)
    for profile in profiles:
        campaigns_to_rename = []
        profile_campaigns = Campaign.objects.filter(
            profile=profile,
            sponsoring_type="sponsoredProducts",
            serving_status__in=CAMPAIGN_VALID_STATUSES,
        ).exclude(campaign_name__contains="Product-Own")
        profile_books = Book.objects.filter(profile=profile)
        # extract all the books from the DB to prevent multiple calls
        profile_books_title = {}
        profile_books_format = {}
        for book in profile_books:
            if book.title != "Book not found on Amazon":
                profile_books_title[book.asin] = book.title
                profile_books_format[book.asin] = book.format.split(sep=" ")[0]
        for campaign in profile_campaigns:
            if len(campaign.asins) == 0:
                _logger.info("Campaign %s has zero ASINs. Couldn't rename.", campaign)
                continue
            asin_in_campaign_name = False
            for asin in campaign.asins:
                if asin in campaign.campaign_name:
                    asin_in_campaign_name = True
                    break
            purpose_in_campaign_name = False
            for purpose in PURPOSE_BOOK_MODEL_MAP:
                if purpose in campaign.campaign_name:
                    purpose_in_campaign_name = True
                    break
            # campaign needs renaming
            if asin_in_campaign_name == False or purpose_in_campaign_name == False:
                book_title_acronym = generate_acronym(profile_books_title[campaign.asins[0]])
                if book_title_acronym == "":
                    _logger.info("Could not generate title acronym for campaign %s.", campaign)
                    continue
                existing_campaigns = Campaign.objects.filter(
                    asins__contains=[campaign.asins[0]],
                    profile=profile,
                    campaign_name__contains=campaign.campaign_purpose,
                    sponsoring_type="sponsoredProducts",
                ).exclude(campaign_name=campaign.campaign_name)
                campaign_count = str(existing_campaigns.count() + 1)
                new_campaign_name = "-".join(
                    (
                        book_title_acronym,
                        "SP",
                        campaign.campaign_purpose,
                        campaign_count,
                        "-".join(campaign.asins),
                        profile_books_format[campaign.asins[0]],
                    )
                )
                campaigns_to_rename.append(
                    CampaignEntity(external_id=campaign.campaign_id_amazon, name=new_campaign_name).dict(
                        exclude_none=True, by_alias=True
                    )
                )

        if len(campaigns_to_rename) > 0:
            campaign_adapter = CampaignAdapter(profile)
            successfully_updated, errors = campaign_adapter.batch_update(campaigns_to_rename)

            if errors:
                _logger.error(
                    "Some compaigns were not updated. Updated [%s], errors [%s]",
                    successfully_updated,
                    errors,
                )
                raise BaseAmazonAdsException(
                    "Some campaigns were not updated. To see additional information, please "
                    f"refer to the logs. Time - {datetime.now()}"
                )


def get_converting_search_terms(book: Book, min_orders: int = 5) -> set[str]:
    """Gets search terms with X+ sales per book over lifetime"""
    search_terms_with_orders = {}  # type: ignore
    converting_search_term_data = RecentReportData.objects.filter(
        campaign__profile=book.profile,
        campaign__asins__contains=[book.asin],
        report_type=SpReportType.KEYWORD_QUERY,
    )
    for datum in converting_search_term_data:
        if datum.query in search_terms_with_orders:
            orders = search_terms_with_orders[datum.query]
            search_terms_with_orders[datum.query] = orders + datum.orders
        else:
            search_terms_with_orders[datum.query] = datum.orders
    converting_search_terms = []
    for query, orders in search_terms_with_orders.items():
        if orders >= min_orders:
            converting_search_terms.append(query)
    return set(converting_search_terms)


def check_for_existing_targets(
    book: Book, targets_to_check: List[str], match_type: str = MatchType.EXACT.value
):
    existing_targets = (
        Keyword.objects.filter(
            match_type=match_type,
            campaign__profile=book.profile,
            campaign__asins__contains=[book.asin],
            keyword_type="Positive",
        )
        .exclude(campaign__state=SpState.ARCHIVED.value)
        .values_list("keyword_text", flat=True)
        .distinct("keyword_text")
    )
    targeted = []
    not_targeted = []
    for target in targets_to_check:
        if target in existing_targets:
            targeted.append(target)
        else:
            not_targeted.append(target)
    return targeted, not_targeted


def get_books_without_autos():
    """Finds books which are being advertised without auto campaigns"""
    pass


def check_campaign_targets_vs_name(profile: Profile, optional_filters: Optional[dict] = None):
    """Checks the campaign name alings with target types within"""
    # get target types per campaign
    # check target type is consistent with campaign name (then extend to campaign purpose check)
    # for profile in profiles:
    model_filters = dict(
        keyword_type="Positive",
        campaign__profile=profile,
        state=SpState.ENABLED.value,
        serving_status__in=TARGETS_VALID_STATUSES,
    )
    if optional_filters:
        model_filters.update(optional_filters)
    all_targets = Keyword.objects.filter(**model_filters).prefetch_related("campaign")
    target_types_per_campaign = defaultdict(list)
    targets_per_book = defaultdict(list)
    for target in all_targets:
        target_types_per_campaign[target.campaign].append(target.match_type)
        targets_per_book[target.campaign.asins[0]].append(target.keyword_text)
    campaigns_to_rename = set()
    for campaign, match_types in target_types_per_campaign.items():
        campaign_name = campaign.campaign_name.lower()
        for match_type in match_types:
            if match_type not in campaign_name:
                campaigns_to_rename.add(campaign)
    return campaigns_to_rename, targets_per_book


@app.task
def campaign_accounting():
    """Turns on management for new campaings, removes paused and archived campaigns from managemend"""
    new_campaigns = Campaign.objects.filter(
        campaign_name__contains="-SP-",
        managed=False,
        profile__managed=True,
        state=SpState.ENABLED.value,
        serving_status__in=CAMPAIGN_VALID_STATUSES,
    )
    new_campaigns.update(managed=True)
    managed_paused_archived_campaigns = Campaign.objects.filter(
        managed=True,
        profile__managed=True,
        state__in=[SpState.PAUSED.value, SpState.ARCHIVED.value],
    )
    managed_paused_archived_campaigns.update(managed=False)


def campaign_roster(asin: str, country_code: str):
    """Counts the number of campaigns with purposes for an ASIN in a market"""
    campaigns = Campaign.objects.filter(
        asins__contains=[asin],
        state=SpState.ENABLED.value,
        serving_status__in=CAMPAIGN_VALID_STATUSES,
        profile__country_code=country_code,
    )
    campaign_counts = {}
    for purpose in CampaignPurpose:  # type: ignore
        campaign_counts[purpose] = 0
    campaign_counts["Unclear purpose"] = 0
    for campaign in campaigns:
        if campaign.campaign_purpose in campaign_counts:
            campaign_counts[campaign.campaign_purpose] += 1
        else:
            campaign_counts["Unclear purpose"] += 1
    _logger.info(
        "%s has %s campaigns running in the %s. The types are as follows:",
        asin,
        campaigns.count(),
        country_code,
    )
    for purpose, count in campaign_counts.items():
        _logger.info("%s: %s", purpose, count)


@app.task
def negate_from_google_sheet():
    """Creates negative exacts as a result of reading 1 column's data"""
    google_sheet = GoogleSheet()
    sheet_instance = google_sheet._get_sheet_object_by_key(worksheet_key=NEGATIVE_ADDITION_SPREADSHEET_ID)
    new_campaign_info_list = google_sheet.get_new_campaign_info(spreadsheet=sheet_instance)
    if len(new_campaign_info_list) < 3:
        _logger.info("No new campaigns info found in Google Sheet inputs.")
        return
    new_campaign_info_dict = _process_read_values(values_from_sheet=new_campaign_info_list)
    asin = new_campaign_info_dict["asin"]
    while len(asin) > 1:
        if len(asin) != 10:
            _logger.error(
                "Length of ASIN: %s was not 10, please check input in Gooogle Sheet.",
                asin,
            )
            return
        book = Book.objects.get(profile__country_code=new_campaign_info_dict["country_code"], asin=asin)
        ###################### MAIN LOGIC ########################
        match_type = new_campaign_info_dict["type"]
        endpoint = SpEndpoint.NEGATIVE_TARGETS if match_type == "asin" else SpEndpoint.NEGATIVE_KEYWORDS
        if match_type == "asin":
            fill_negative_targets_service = FillWithNegativeTargetsService(book)
            created, errors = fill_negative_targets_service.fill_with_negatives(
                text_negatives=new_campaign_info_dict["targets"],
                predicate_type=NegativeTargetingExpressionPredicateType.ASIN_SAME_AS,
            )
            _logger.info("Created negative targets: %s, errors: %s", created, errors)
        else:
            fill_negative_keywords_service = FillWithNegativeKeywordsService(book)
            created, errors = fill_negative_keywords_service.fill_with_negatives(
                text_negatives=new_campaign_info_dict["targets"],
                match_type=new_campaign_info_dict["type"],
            )
            _logger.info("Created negative keywords: %s, errors: %s", created, errors)

        ##########################################################
        # add created timestamp information to the info to be moved
        while len(new_campaign_info_list) < 5:
            new_campaign_info_list.append("")
        new_campaign_info_list[4] = f"Created: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}"
        # move data from input to output sheet
        google_sheet.move_created_campaign_to_output(
            campaign_info=new_campaign_info_list, spreadsheet=sheet_instance
        )
        # fetch new data to possibly start another loop
        new_campaign_info_list = google_sheet.get_new_campaign_info(spreadsheet=sheet_instance)
        if len(new_campaign_info_list) < 3:
            break
        new_campaign_info_dict = _process_read_values(values_from_sheet=new_campaign_info_list)
        asin = new_campaign_info_dict["asin"]
        # Preventive sleep to avoid throttling
        time.sleep(10)
    _logger.info("Negatives successfully added using Google Sheet inputs.")


@app.task
def get_keyword_rank_from_google_sheets():
    """Get keyword rank for keywords and books in Google Sheet"""
    google_sheet = GoogleSheet()
    sheet_instance = google_sheet._get_sheet_object_by_key(worksheet_key=RANK_TRACKER_SPREADSHEET_ID)
    # get books, markets and keywords from Google Sheet
    rank_check_data = google_sheet.get_rank_check_info(spreadsheet=sheet_instance)
    updated_rank_data = []
    # get all asins per market
    all_asins = set()
    for row_data in rank_check_data:
        all_asins.add(row_data[2])
    books = Book.objects.filter(asin__iregex=r"(" + "|".join(all_asins) + ")").prefetch_related("profile")

    book_mem: Dict[str, Book] = {}
    for book in books:
        book_mem[book.profile.country_code + book.asin] = book

    asins_per_url = {}

    # get asins on page 1
    for row_data in rank_check_data:
        country_code = row_data[1]
        asin = row_data[2].upper()
        keyword = row_data[3].lower().replace(" ", "+")
        try:
            book = book_mem[country_code + asin]
        except KeyError:
            _logger.info("ASIN not in db: %s, country code: %s", asin, country_code)
            continue

        # search in Books on Amazon
        domain = DOMAINS.get(book.profile.country_code)
        proxy_location = "gb" if book.profile.country_code == "UK" else book.profile.country_code.lower()
        search_category = "&i=stripbooks" if book.format == "Paperback" else "&i=digital-text"
        url = f"https://www.amazon.{domain}/s?k={keyword}{search_category}"

        if asins_per_url.get(url) is not None:
            sb_asins, sp_asins, organic_asins = asins_per_url[url]
        else:
            response = get_html_via_proxy(url=url, proxy_location=proxy_location)
            # go to the next book is the scrape failed
            if response is None:
                updated_rank_data.append(row_data)
                continue
            sb_asins, sp_asins, organic_asins = extract_asins_from_html(html_text=response.text)
            asins_per_url[url] = (sb_asins, sp_asins, organic_asins)

        # get asins on page 2, if necessary
        if asin not in sp_asins or asin not in organic_asins:
            page_2_url = f"{url}&page=2"
            if asins_per_url.get(page_2_url) is not None:
                _, more_sp_asins, more_organic_asins = asins_per_url[page_2_url]
                sp_asins.extend(more_sp_asins)
                organic_asins.extend(more_organic_asins)
            else:
                response = get_html_via_proxy(url=page_2_url, proxy_location=proxy_location)
                if response:
                    (_, more_sp_asins, more_organic_asins) = extract_asins_from_html(html_text=response.text)

                    sp_asins.extend(more_sp_asins)
                    organic_asins.extend(more_organic_asins)
                    asins_per_url[page_2_url] = (_, more_sp_asins, more_organic_asins)

        # check for presence of ASIN you're checking
        rank_dict = {}
        for col, rank_model_field, temp_list in [
            (4, "rank_sb", sb_asins),
            (5, "rank_sp", sp_asins),
            (6, "rank_org", organic_asins),
        ]:
            if asin in temp_list:
                row_data[col] = temp_list.index(asin) + 1
                rank_dict[rank_model_field] = temp_list.index(asin) + 1
            else:
                row_data[col] = ""
        # update the Rank model
        if len(rank_dict) > 0:
            Rank.objects.update_or_create(
                book=book,
                keyword=keyword.replace("+", " "),
                defaults=rank_dict,
            )
        row_data[7] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        updated_rank_data.append(row_data)
    # write to Google Sheet, from the top (as new keywords and ASINs may be added during the checking operation)
    google_sheet.write_rank_check_info(spreadsheet=sheet_instance, data_to_write=updated_rank_data)
    _logger.info("get_keyword_rank_from_google_sheets is complete")


def negate_exacts_in_research_campaigns(profiles: Optional[QuerySet[Profile]] = None):
    """Adds existing Exact targets & ASINs as negative exacts to Research & Discovery campaigns"""
    profiles = Profile.objects.filter(managed=True) if profiles is None else profiles
    for profile in profiles:
        for (
            endpoint,
            exact_campaign_purposes,
            research_campaign_purposes,
            exact_filter,
        ) in [
            (
                SpEndpoint.NEGATIVE_TARGETS,
                [CampaignPurpose.Product_Comp, CampaignPurpose.Product_Own],
                [CampaignPurpose.Discovery, CampaignPurpose.Cat_Research],
                dict(targeting_type=SpExpressionType.MANUAL.value),
            ),
            (
                SpEndpoint.NEGATIVE_KEYWORDS,
                [CampaignPurpose.Exact_Scale, CampaignPurpose.Exact_Scale_Single],
                [
                    CampaignPurpose.Discovery,
                    CampaignPurpose.Broad_Research,
                    CampaignPurpose.Broad_Research_Single,
                ],
                dict(match_type=MatchType.EXACT.value),
            ),
        ]:
            model, identifier, _ = _set_keyword_filters(endpoint=endpoint)
            if not model or not identifier or not _:
                _logger.info(
                    "Count not identify model, identifier, keyword_type for profile: %s [%s]",
                    profile.nickname,
                    profile.country_code,
                )
                return
            # get all Exacts & ASINs per book in profile
            exacts_per_book: Dict[str, List[str]] = {}
            existing_exacts = model.objects.filter(
                campaign__campaign_purpose__in=exact_campaign_purposes,
                campaign__profile=profile,
                keyword_type="Positive",
                **exact_filter,
            )
            for existing_exact in existing_exacts:
                for asin in existing_exact.campaign.asins:
                    if asin in exacts_per_book:
                        exacts_in_asin = exacts_per_book[asin]
                        if getattr(existing_exact, identifier).lower() not in exacts_in_asin:
                            exacts_in_asin.append(getattr(existing_exact, identifier).lower())
                            exacts_per_book[asin] = exacts_in_asin
                    else:
                        exacts_per_book[asin] = [getattr(existing_exact, identifier).lower()]

            # get all negatives per book in profile
            existing_negatives = model.objects.filter(
                campaign__campaign_purpose__in=research_campaign_purposes,
                campaign__profile=profile,
                campaign__sponsoring_type="sponsoredProducts",
                keyword_type="Negative",
                state=SpState.ENABLED.value,
            )
            negatives_per_ad_group: Dict[str, List[str]] = {}
            for existing_negative in existing_negatives:
                ad_group = existing_negative.ad_group_id
                if ad_group in negatives_per_ad_group:
                    _negatives_list = negatives_per_ad_group[ad_group]
                    if getattr(existing_negative, identifier).lower() not in _negatives_list:
                        _negatives_list.append(getattr(existing_negative, identifier).lower())
                        negatives_per_ad_group[ad_group] = _negatives_list
                else:
                    negatives_per_ad_group[ad_group] = [getattr(existing_negative, identifier).lower()]
            # ad groups per book
            valid_ads = ProductAd.objects.filter(
                campaign__campaign_purpose__in=research_campaign_purposes,
                campaign__profile=profile,
                campaign__managed=True,
                campaign__sponsoring_type="sponsoredProducts",
                campaign__serving_status__in=CAMPAIGN_VALID_STATUSES,
                state=SpState.ENABLED.value,
            ).exclude(ad_group__serving_status__in=AD_GROUP_INVALID_STATUSES)
            ad_groups_per_book: Dict[str, List[str]] = {}
            for valid_ad in valid_ads:
                for asin in valid_ad.campaign.asins:
                    if asin in ad_groups_per_book:
                        ad_groups = ad_groups_per_book[asin]
                        if valid_ad.ad_group.ad_group_id not in ad_groups:
                            ad_groups.append(valid_ad.ad_group.ad_group_id)
                            ad_groups_per_book[asin] = ad_groups
                    else:
                        ad_groups_per_book[asin] = [valid_ad.ad_group.ad_group_id]
            # create an ad group id to campaign id map
            ad_group_id_campaign_id_map: Dict[str, str] = {}
            for valid_ad in valid_ads:
                ad_group_id = valid_ad.ad_group.ad_group_id
                if ad_group_id not in ad_group_id_campaign_id_map:
                    ad_group_id_campaign_id_map[ad_group_id] = valid_ad.campaign.campaign_id_amazon
            keywords_array = []
            # if search term is not already added as negative, add as negative exact per book in profile
            for asin, exacts in exacts_per_book.items():
                if asin not in ad_groups_per_book:
                    continue
                ad_groups = ad_groups_per_book[asin]
                for ad_group in ad_groups:
                    negatives_list = (
                        negatives_per_ad_group[ad_group] if ad_group in negatives_per_ad_group else []
                    )
                    for exact in exacts:
                        if exact not in negatives_list:
                            request_body = BodyDict(
                                endpoint=endpoint,
                                campaign_id=ad_group_id_campaign_id_map[ad_group],
                                ad_group_id=ad_group,
                                target_text=exact,
                            )
                            keywords_array.append(request_body.value)
            if len(keywords_array) > 0:
                AdsAPI.add_sp_data(
                    server=profile.profile_server,
                    profile_id=profile.profile_id,
                    data_dicts_array=keywords_array,
                    endpoint=endpoint,
                )
                _logger.info(
                    "Negated %s %ss on %s",
                    len(keywords_array),
                    model._meta.model_name,
                    profile,
                )  # type: ignore


def _sum_report_data(query_data: QuerySet[RecentReportData], query_data_filters: Dict) -> AdSlice:
    """Produce a sum of ReportData as an AdSlice dataclass"""
    current_query_total = query_data.filter(**query_data_filters).aggregate(
        sales=Coalesce(Sum("sales"), V(0), output_field=DecimalField()),
        spend=Coalesce(Sum("spend"), V(0), output_field=DecimalField()),
        kenp_royalties=Coalesce(Sum("kenp_royalties"), V(0), output_field=DecimalField()),
        impressions=Coalesce(Sum("impressions"), V(0), output_field=DecimalField()),
        clicks=Coalesce(Sum("clicks"), V(0), output_field=DecimalField()),
    )
    current_query_summary = AdSlice(
        float(current_query_total["sales"]),
        float(current_query_total["spend"]),
        current_query_total["kenp_royalties"],
        current_query_total["impressions"],
        current_query_total["clicks"],
        0,
    )
    return current_query_summary


def _rank_targets(ids: List[int], all_ad_slices: Dict[int, AdSlice]):
    """Takes ids of targets and compares their performance returning the best target id as int and the rest as a list of ints"""
    all_target_data = {}
    for current_id in sorted(ids):
        if current_id == 0:
            best_id = 0
            ids.remove(0)
            return best_id, ids
        target_summary = all_ad_slices[current_id]
        all_target_data[current_id] = target_summary
    data_list = []
    for current_id, data in sorted(all_target_data.items()):
        data_list.append(data.sales)
    max_sales = max(data_list)
    count = data_list.count(max_sales)
    best_index = data_list.index(max_sales)
    if count > 1:
        i = 0
        sales_positions = defaultdict(list)
        for v in data_list:
            sales_positions[v].append(i)
            i += 1
        best_pos_list = sales_positions[max_sales]
        spends = []
        i = 0
        for current_id, data in sorted(all_target_data.items()):
            if i in best_pos_list:
                spends.append(data.spend)
            i += 1
        index_spend = spends.index(min(spends)) if max_sales > 0 else spends.index(max(spends))
        best_index = best_pos_list[index_spend]
    i = 0
    best_id = 0
    others = []
    for current_id, data in sorted(all_target_data.items()):
        if i == best_index:
            best_id = current_id
        else:
            others.append(current_id)
        i += 1
    return best_id, others


@app.task
def deduplicate_targets(profile_ids: Optional[list[int]] = None):
    """Pauses lower performance duplicate targets for profile"""
    if profile_ids:
        profiles = Profile.objects.filter(id__in=profile_ids)
    else:
        profiles = Profile.objects.filter(managed=True)

    for profile in profiles:
        for model, endpoint, type, text, ident, identifier_amazon in [
            (
                Keyword,
                SpEndpoint.KEYWORDS,
                "match_type",
                "keyword_text",
                "keyword_id",
                "keywordId",
            ),
            (
                Target,
                SpEndpoint.TARGETS,
                "resolved_expression_type",
                "resolved_expression_text",
                "target_id",
                "targetId",
            ),
        ]:
            # get all targets
            targets = (
                model.objects.filter(  # type: ignore
                    campaign__profile=profile,
                    state=SpState.ENABLED.value,
                    serving_status__in=TARGETS_VALID_STATUSES,
                    keyword_type="Positive",
                )
                .exclude(campaign__campaign_purpose=CampaignPurpose.GP)
                .exclude(campaign__campaign_purpose=CampaignPurpose.Auto_GP)
                .exclude(campaign__campaign_name__contains="-GP-")
                .prefetch_related("campaign")
            )
            # strucutre ASIN, Match Type, Keyword text, keyword id
            grouped_targets = defaultdict(list)
            for target in targets:
                db_ident = (
                    0
                    if target.campaign.campaign_purpose
                    in [
                        CampaignPurpose.Broad_Research_Single,
                        CampaignPurpose.Exact_Scale_Single,
                    ]
                    or "-Single" in target.campaign.campaign_name
                    else getattr(target, ident)
                )
                asins = target.campaign.asins  # Django caches the DB query
                for asin in asins:
                    grouped_targets[f"{asin}-{getattr(target, type)}-{getattr(target, text)}"].append(
                        db_ident
                    )
            ids_to_pause = []
            _logger.info(
                "%ss to analyse on %s: %s",
                model._meta.model_name,
                profile,
                len(grouped_targets),
            )  # type: ignore
            all_ids = []
            for info, ids in grouped_targets.items():
                if len(ids) > 1 and 0 not in ids:
                    all_ids.extend(ids)
            if len(all_ids) == 0:
                continue
            additional_filter = {ident + "__in": all_ids}
            query_data = RecentReportData.objects.filter(
                Q(sales__gt=0)
                | Q(spend__gt=0)
                | Q(kenp_royalties__gt=0)
                | Q(impressions__gt=0)
                | Q(clicks__gt=0)
                | Q(orders__gt=0),
                campaign__profile=profile,
                **additional_filter,
            )
            all_ad_slices: Dict[int, AdSlice] = defaultdict(AdSlice)
            for report_datum in query_data:
                all_ad_slices[getattr(report_datum, ident)].add(
                    AdSlice(
                        sales=report_datum.sales,
                        spend=report_datum.spend,
                        kenp_royalties=report_datum.kenp_royalties,
                        impressions=report_datum.impressions,
                        clicks=report_datum.clicks,
                        orders=report_datum.orders,
                    )
                )
            empty_slice = AdSlice(0.0, 0.0, 0, 0, 0, 0)
            for id in all_ids:
                all_ad_slices[id].add(empty_slice)
            for info, ids in grouped_targets.items():
                if len(ids) > 1:
                    # analyse performance of Keywords or Targets
                    best, others = _rank_targets(ids=ids, all_ad_slices=all_ad_slices)
                    ids_to_pause.extend(others)
            if len(ids_to_pause) > 0:
                targets_to_pause = []
                Entity, Adapter = (
                    (KeywordEntity, KeywordsAdapter) if model is Keyword else (TargetEntity, TargetsAdapter)
                )
                for current_id in ids_to_pause:
                    targets_to_pause.append(
                        Entity.parse_obj({"external_id": current_id, "state": SpState.PAUSED}).dict(
                            exclude_none=True, by_alias=True
                        )
                    )
                adapter = Adapter(profile)
                adapter.batch_update(targets_to_pause)
                _logger.info("Paused %s %ss on %s", len(ids_to_pause), model._meta.model_name, profile)  # type: ignore


def check_campaign_names():
    profile = Profile.objects.get(nickname="TimZ", country_code="UK")
    campaigns = Campaign.objects.filter(profile=profile)
    wrongly_named_campaigns = set()
    for c in campaigns:
        asins = c.asins
        if len(asins) == 0:
            continue
        name = c.campaign_name
        for asin in asins:
            if asin not in name and "dverio" not in name:
                wrongly_named_campaigns.add(name)
    _logger.info(wrongly_named_campaigns)


def clean_up_broad_campaigns(profiles: Optional[QuerySet[Profile]] = None):
    # get all -Broad- campaigns which have exact keywords for managed profiles
    profiles = Profile.objects.filter(managed=True) if profiles is None else profiles
    for profile in profiles:
        campaigns_to_rename, targets_per_book = check_campaign_targets_vs_name(
            profile=profile,
            optional_filters=dict(
                campaign__campaign_name__contains="-Broad-",
                match_type=MatchType.EXACT.value,
            ),
        )
        # save those campaigns as a TXT file
        if len(campaigns_to_rename) == 0:
            continue
        with open(f"TXT\\{profile}.txt", "w") as f:
            f.write(str(targets_per_book))
        # for each of those campaigns, create a new name
        all_campaign_names = (
            Campaign.objects.filter(profile=profile)
            .order_by("campaign_name")
            .values_list("campaign_name", flat=True)
            .distinct("campaign_name")
        )
        campaigns_to_rename_amazon_list = []
        # check if that name already exists
        # print(campaigns_to_rename)
        for campaign in campaigns_to_rename:
            new_campaign_name = str(campaign.campaign_name).replace("-Broad-Research", "-Exact-Scale")
            # if yes, add a 2 onto the end of the name and rename to Exact
            if new_campaign_name in all_campaign_names:
                new_campaign_name = new_campaign_name + "2"
            campaigns_to_rename_amazon_list.append(
                CampaignEntity(external_id=campaign.campaign_id_amazon, name=new_campaign_name).dict(
                    exclude_none=True, by_alias=True
                )
            )
        # update on Amazon
        if len(campaigns_to_rename_amazon_list) > 0:
            campaign_adapter = CampaignAdapter(profile)
            successfully_updated, errors = campaign_adapter.batch_update(campaigns_to_rename_amazon_list)
            if errors:
                _logger.error(
                    "Some compaigns were not updated. Updated [%s], errors [%s]",
                    successfully_updated,
                    errors,
                )
                raise BaseAmazonAdsException(
                    "Some campaigns were not updated. To see additional information, please "
                    f"refer to the logs. Time - {datetime.now()}"
                )

@app.task
def clean_up_ended_campaigns():
    Campaign.objects.filter(
        serving_status=BaseServingStatus.ENDED.value,
        managed=True
    ).update(managed=False)

def add_negatives_per_asin(
    text_negatives: List[str],
    endpoint: SpEndpoint,
    book: Book,
    match_type: Optional[str] = MatchType.EXACT,
):
    """Adds negative phrase & exacts per book in profile (market)"""
    if match_type == "exact":
        match_type = NegativeMatchType.EXACT
    elif match_type == "phrase":
        match_type = NegativeMatchType.PHRASE

    if endpoint == SpEndpoint.NEGATIVE_KEYWORDS and match_type not in [
        NegativeMatchType.EXACT,
        NegativeMatchType.PHRASE,
    ]:
        _logger.error("Invalid match type: %s passed to negatives function", match_type)
        raise TypeError(
            (
                f"Invalid match type: {match_type}. "
                f"Allowed match types {[NegativeMatchType.EXACT, NegativeMatchType.PHRASE, ]}"
            )
        )
    cleaner = KeywordsCleanerService(keywords=text_negatives)

    if endpoint == SpEndpoint.NEGATIVE_KEYWORDS:
        adapter = NegativeKeywordsAdapter(book.profile)
        model = Keyword
        ident = "keyword_text"
        text_negatives = cleaner.clean_keywords(marketplace=book.profile.country_code)
    elif endpoint == SpEndpoint.NEGATIVE_TARGETS:
        adapter = NegativeTargetsAdapter(book.profile)
        model = Target
        ident = "resolved_expression_text"
        text_negatives = cleaner.clean_keywords(is_asins=True)
    else:
        _logger.error("Invalid endpoint: %s passed to negatives function", endpoint)
        raise TypeError(f"Invalid endpoint: {endpoint} passed to negatives function")
    book_ad_groups = (
        AdGroup.objects.filter(
            campaign__serving_status__in=CAMPAIGN_VALID_STATUSES,
            campaign__sponsoring_type="sponsoredProducts",
            state=SpState.ENABLED.value,
            campaign__books__asin=book.asin,
        )
        .exclude(
            Q(serving_status__in=AD_GROUP_INVALID_STATUSES)
            | Q(campaign__campaign_name__contains="-Exact-")
            | Q(campaign__campaign_name__contains="-Product-")
            | Q(campaign__campaign_name__contains="-GP-")
        )
        .select_related("campaign")
        .order_by("ad_group_id")
        .distinct("ad_group_id")
    )
    if not book_ad_groups.exists():
        return

    ad_group_ids_list = book_ad_groups.values_list("ad_group_id", flat=True)
    negatives = model.objects.filter(
        keyword_type="Negative",
        state=SpState.ENABLED.value,
        ad_group_id__in=ad_group_ids_list,
    )

    db_negative_text_per_ad_group = defaultdict(list)
    for negative in negatives:
        db_negative_text_per_ad_group[negative.ad_group_id].append(getattr(negative, ident).lower())

    negatives_to_create = []
    for negative_text in text_negatives:
        for ad_group in book_ad_groups:
            if negative_text not in db_negative_text_per_ad_group[ad_group]:
                if model is Keyword:
                    keyword_entity = NegativeKeywordEntity(
                        campaign_id=book_ad_groups.campaign.campaign_id_amazon,
                        ad_group_id=ad_group.ad_group_id,
                        match_type=NegativeMatchType.PHRASE if match_type else NegativeMatchType.EXACT,
                        keyword_text=negative_text,
                        state=SpState.ENABLED,
                    )
                else:
                    keyword_entity = NegativeTargetEntity(
                        campaign_id=book_ad_groups.campaign.campaign_id_amazon,
                        ad_group_id=ad_group.ad_group_id,
                        expression=[
                            Expression(
                                type=NegativeTargetingExpressionPredicateType.ASIN_SAME_AS,
                                value=negative_text,
                            )
                        ],
                        state=SpState.ENABLED,
                    )

                negatives_to_create.append(keyword_entity.dict(exclude_none=True, by_alias=True))

    created, errors = adapter.batch_create(negatives_to_create)
    if errors:
        _logger.error(f"Negative keywords/targets were not created successfully {errors}")
        raise ObjectNotCreatedError(errors)


def check_targets_and_keywords_not_updated_in_48_hours() -> None:
    """Checks targets and keywords which have not been updated in 48 hours."""
    two_days_ago = (timezone.now() - timezone.timedelta(hours=48)).timestamp() * 1000

    campaign_filters = (
        Q(campaign__campaign_name__contains="-GP-")
        | Q(campaign__campaign_name__contains="_GP_")
        | Q(campaign__campaign_purpose__in=[CampaignPurpose.GP, CampaignPurpose.Auto_GP])
    )

    counts = []
    for model in [Target, Keyword]:
        count = (
            model.objects.filter(last_updated_date_on_amazon__lte=two_days_ago, campaign__managed=True)
            .exclude(campaign_filters)
            .count()
        )
        counts.append(count)

    _logger.info(f"Found {counts[0]} targets not updated in 48 hours")
    _logger.info(f"Found {counts[1]} keywords not updated in 48 hours")


#############################################################################################
##################################### CELERY TASKS ##########################################
#############################################################################################


@app.task
def sp_chain():
    """Helper Celery chaining task to sync Sponsored Products ads via Ads API"""
    tasks = (
        sync_profiles.si()
        | sync_campaigns.si()
        | sync_ad_groups.si()
        | sync_product_ads.si()
        | sync_keywords.si()
        | clean_up_ended_campaigns.si()
        | update_bids_for_managed.si()
        | get_asins_for_sp_campaigns.si()
        | classify_ad_groups.si()
        | campaign_clean_up.si()
        | sp_campaign_purpose_update.si()
        | fill_out_associated_sp_campaigns_in_book_model.si()
        | update_profit_campaign_budgets.si()
        | clean_up_old_reports.si()
        | mark_targeted_relevancy.si()
        | campaign_accounting.si()
    )
    chain(tasks).apply_async()  # type: ignore


@app.task
def sp_requests_chain():
    """Helper Celery chaining task to sync Sponsored Products ads via requests"""
    tasks = get_profile_book_catalog.si() | update_books_details.si() | recalculate_acos.si()
    chain(tasks).apply_async()  # type: ignore


@app.task
def sb_requests_chain():
    """Helper Celery chaining task to sync Sponsored Brands ads via requests"""
    tasks = sync_brand_campaigns.si() | adjust_brand_bids.si() | add_brand_negative_exacts.si()
    chain(tasks).apply_async()  # type: ignore


#############################################################################################
##################################### TESTING AREA ##########################################
#############################################################################################


# sp_data_sync_days(days=14)

# sync_profiles()
# sync_campaigns()
# sync_ad_groups()
# sync_product_ads()
# sync_keywords()
# sync_keywords(profiles=Profile.objects.filter(nickname="MicheleBina", country_code="US"))

# get_profile_book_catalog()

# get_asins_for_sp_campaigns()
# update_book_model()

# book_info.fill_out_book_info()
# # book_info.fill_out_book_info(
# #     profile=Profile.objects.get(nickname="Matheus", country_code="US"), force=True
# # )  # on SP_API app

# classify_ad_groups()
# managed_campaigns_for_managed_books()  ###!!!###  this may turn off managed campaigns which are not in managed books

# sp_campaign_purpose_update()
# # NOTE: new account was OK until here but new books being added were all managed which began to create new unwanted campaigns
# fill_out_associated_sp_campaigns_in_book_model()  ###!!!###  this will create new campaigns

# sp_data_sync_days(days=35, days_end=1)
# sp_data_sync_days(days=35, days_end=4, force_re_run=True)
# sp_data_sync_days(
#     days=30, force_re_run=True, managed_profiles=Profile.objects.filter(nickname="MeganFerry", country_code="US")
# )  # , force_re_run=True)

# sp_check_reports()
# sp_process_reports()

# # fill_out_sp_negatives() ###!!!###  this will create lots of negatives
# process_sp_queries()
# udpate_sp_bids_status()
# udpate_sp_placements(profiles=Profile.objects.filter(nickname="TimZ", managed=True))
# reset_gp_bids()
# campaign_budget_check()

# sync_brand_campaigns()
# adjust_brand_bids()
# add_brand_negative_exacts()
# campaign_clean_up()


# #### To Check #### #

# add_asins_to_profile(make
#     asins_to_add=[],
#     profiles=Profile.objects.filter(nickname="Dylan"),
# )
# set_campaigns_target_acos()

# run_reports_new_profiles()

# _get_brand_campaigns(entity_id="ENTITY2WP38ZSN9QGSB", country_code="US")

# target_checked_new_releases()

# get_profitable_target_books_to_check_relevance()
# mark_targeted_relevancy()

# countries = ["US", "CA", "UK"]
# countries = ["CA", "UK"]
# countries = ["US", "UK"]
# countries = ["CA", "UK"]
# countries = ["US"]
# asins = [
#     "B08FP5TXMH",
# ]

# purposes = [CampaignPurpose.Broad_Research_Single, CampaignPurpose.Exact_Scale_Single]

# for purpose in purposes:
#     for country_code in countries:
#         for asin in asins:
#             create_single_keyword_campaigns(
#                 book=Book.objects.get(profile__country_code=country_code, asin=asin),
#                 keywords=["short stories for kids"],
#                 campaign_purpose=purpose,
#             )


# for country_code in countries:
#     for asin in asins:
#         create_split_auto_campaigns(book=Book.objects.get(profile__country_code=country_code, asin=asin))

# add_ASIN_campaign_name(profiles=Profile.objects.filter(nickname="YanVinarskiy"))
# get_number_pages_for_books()
#     books_to_process=Book.objects.filter(
#         profile=Profile.objects.get(nickname="MarcMorgan", country_code="US"),
#         format="Paperback",
#         in_catalog=True,
#     )
# )
# turn_on_profit_mode(profiles=Profile.objects.filter(nickname="EdOsuagwu"))
# new_client_sync(profiles=Profile.objects.filter(nickname="RandAlexander"))
# rename_campaigns_standard(profiles=Profile.objects.filter(nickname="AntonioDiSano"))

# for asin in asins:
#     converting_search_terms = get_converting_search_terms(book=Book.objects.get(profile__country_code="UK", asin=asin))
#     print(f"Converting search terms for {asin}: {converting_search_terms}")

# asin="1692044486"
# converting_search_terms = get_converting_search_terms(book=Book.objects.get(profile__country_code="US", asin=asin))
# print(f"Converting search terms for {asin}: {converting_search_terms}")

# check_campaign_targets_vs_name(profiles=Profile.objects.filter(nickname="JoshLiu", country_code="UK"))
# campaign_accounting()

# for asin in asins:
#     campaign_roster(asin=asin, country_code="US")


# negate_from_google_sheet()
# negate_exacts_in_research_campaigns(profiles=Profile.objects.filter(nickname="CJ", country_code="US"))
# deduplicate_targets()

# check_campaign_names()

# profiles_list = [
#     "LionelKubwimana",
# ]
# new_client_sync(profiles=Profile.objects.filter(nickname__in=profiles_list))
# get_profile_book_catalog(profiles=Profile.objects.filter(nickname__in=profiles_list))
# profiles = Profile.objects.filter(nickname__in=profiles_list, country_code="UK")
# clean_up_broad_campaigns(profiles=profiles)

# create_campaign_from_google_sheet()

# get_keyword_rank_from_google_sheets()

# get_number_pages_for_books()
# recalculate_acos()
