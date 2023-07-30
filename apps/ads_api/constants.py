import os
from enum import Enum
from typing import NamedTuple

# from apps.ads_api.models import CampaignPurpose
# from apps.ads_api.models import CountryCodeChoice

DEFAULT_BUDGETING_DAYS = 30
MIN_MONTHLY_BUDGET = 500
DEFAULT_DAILY_BUDGET = 20.01
DEFAULT_BOOK_PRICE = 9.99
DEFAULT_EBOOK_PRICE = 2.99
MIN_BE_ACOS = 0.2
DEFAULT_BE_ACOS = 0.4
DEFAULT_BE_ACOS_KINDLE = 0.7
DEFAULT_ROYALTY = 3.99
DEFAULT_PRINTING_COST = 3.99
DEFAULT_DATA_TIMEFRAME_DAYS = 30
MAX_DATA_TIMEFRAME_DAYS = 90
DEFAULT_DATA_ACCURACY_CUTOFF_DAYS = 2
DEFAULT_MIN_BID = 0.11
DEFAULT_MAX_BID = 1.51
DEFAULT_MAX_FILTER_BID = 3.5
DEFAULT_MAX_BID_CONSERVATIVE = 0.33
DEFAULT_BID = 0.67
DEFAULT_CPC = 0.67
DEFAULT_BOOK_LENGTH = 150
GP_MAX_BID = 0.2

KDP_HIGHER_ROYALTY = 0.7
KDP_LOWER_ROYALTY = 0.35
BOOK_ROYALTY_RATE = 0.6

MIN_KENP_ROYALTIES_MULTIPLIER = 0.5
MIN_ORDERS_ST_GRADUATION = 2
RESEARCH_MARGIN_MULTIPLIER = 1.1
PROFITABLE_TARGET_CHUNK_DAYS = 10
BID_LOWER_THRESHOLD = 0.6
BID_UPPER_THRESHOLD = 2.5
MIN_BOOK_REVIEWS = 5

MAX_KEYWORDS_API_RESPONSE = 5000
EMPTY_REPORT_BYTES = 22
MIN_SALES_FOR_BID_CHANGE_DATA = 5
CAMPAIGNS_PER_TARGETS_REQUEST = 400
MAX_PROFITABLE_BSR = 100000

SCRAPE_OPS_KEY = os.getenv("SCRAPE_OPS_KEY", "")
SCRAPE_OPS_BASE_URL = "http://proxy.scrapeops.io/v1/"
MIN_RESULTS_PER_AMAZON_SEARCH_PAGE = 20

CAMPAIGN_CREATION_SPREADSHEET_ID = os.getenv("CAMPAIGN_CREATION_SPREADSHEET_ID", "")
NEGATIVE_ADDITION_SPREADSHEET_ID = os.getenv("NEGATIVE_ADDITION_SPREADSHEET_ID", "")
RANK_TRACKER_SPREADSHEET_ID = os.getenv("RANK_TRACKER_SPREADSHEET_ID", "")

TOS_SINGLE_KEYWORD_CAMPAIGNS = 50

BIG_BID_CHANGE = 0.11
SML_BID_CHANGE = 0.06
IMP_TRESHOLD = 1000
PAUSE_TRESHOLD = 20

CATALOG_PAGE_LIMIT = 100


class CampaignType(str, Enum):
    SPONSORED_PRODUCTS = "sponsoredProducts"

    def __str__(self):
        return str(self.value)


class CampaignRetryStrategy(str, Enum):
    RECREATE = "RECREATE"
    FILL_UP_WITH_KEYWORDS = "FILL_UP_WITH_KEYWORDS"

    def __str__(self):
        return self.value


class CampaignTargetingType(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"

    def __str__(self):
        return str(self.value)


class QueryTermMatchType(str, Enum):
    BROAD_MATCH = "BROAD_MATCH"
    EXACT_MATCH = "EXACT_MATCH"

    def __str__(self):
        return str(self.value)


class BidRecommendationType(Enum):
    BIDS_FOR_EXISTING_AD_GROUP = "BIDS_FOR_EXISTING_AD_GROUP"

    def __str__(self):
        return str(self.value)


class TargetingExpressionType(Enum):
    CLOSE_MATCH = "CLOSE_MATCH"
    LOOSE_MATCH = "LOOSE_MATCH"
    SUBSTITUTES = "SUBSTITUTES"
    COMPLEMENTS = "COMPLEMENTS"
    KEYWORD_BROAD_MATCH = "KEYWORD_BROAD_MATCH"
    KEYWORD_EXACT_MATCH = "KEYWORD_EXACT_MATCH"
    KEYWORD_PHRASE_MATCH = "KEYWORD_PHRASE_MATCH"

    def __str__(self):
        return str(self.value)


class MatchType(str, Enum):
    EXACT = "EXACT"
    PHRASE = "PHRASE"
    BROAD = "BROAD"
    OTHER = "OTHER"

    def __str__(self):
        return str(self.value)


class NegativeMatchType(str, Enum):
    EXACT = "NEGATIVE_EXACT"
    PHRASE = "NEGATIVE_PHRASE"
    BROAD = "NEGATIVE_BROAD"
    OTHER = "OTHER"

    def __str__(self):
        return str(self.value)


class BaseServingStatus(Enum):
    ADVERTISER_OUT_OF_BUDGET = "ADVERTISER_OUT_OF_BUDGET"
    ADVERTISER_PAYMENT_FAILURE = "ADVERTISER_PAYMENT_FAILURE"
    ADVERTISER_POLICING_PENDING_REVIEW = "ADVERTISER_POLICING_PENDING_REVIEW"
    CAMPAIGN_OUT_OF_BUDGET = "CAMPAIGN_OUT_OF_BUDGET"
    CAMPAIGN_STATUS_ENABLED = "CAMPAIGN_STATUS_ENABLED"
    PENDING_REVIEW = "PENDING_REVIEW"
    PENDING_START_DATE = "PENDING_START_DATE"
    PORTFOLIO_OUT_OF_BUDGET = "PORTFOLIO_OUT_OF_BUDGET"
    PORTFOLIO_PENDING_START_DATE = "PORTFOLIO_PENDING_START_DATE"
    PORTFOLIO_STATUS_ENABLED = "PORTFOLIO_STATUS_ENABLED"
    ADVERTISER_ARCHIVED = "ADVERTISER_ARCHIVED"
    ADVERTISER_PAUSED = "ADVERTISER_PAUSED"
    ADVERTISER_POLICING_SUSPENDED = "ADVERTISER_POLICING_SUSPENDED"
    CAMPAIGN_ARCHIVED = "CAMPAIGN_ARCHIVED"
    CAMPAIGN_INCOMPLETE = "CAMPAIGN_INCOMPLETE"
    CAMPAIGN_PAUSED = "CAMPAIGN_PAUSED"
    ENDED = "ENDED"
    OTHER = "OTHER"
    PORTFOLIO_ARCHIVED = "PORTFOLIO_ARCHIVED"
    PORTFOLIO_ENDED = "PORTFOLIO_ENDED"
    PORTFOLIO_PAUSED = "PORTFOLIO_PAUSED"
    REJECTED = "REJECTED"

    def __str__(self):
        return str(self.value)


def __str__(self):
    return self.value


CampaignServingStatus = Enum(
    value="CampaignServingStatus",
    names=[(i.name, str(i.value)) for i in BaseServingStatus]
    + [("ACCOUNT_OUT_OF_BUDGET", "ACCOUNT_OUT_OF_BUDGET")],
)

CampaignServingStatus.__str__ = __str__

AdGroupServingStatus = Enum(
    value="AdGroupServingStatus",
    names=[(i.name, str(i.value)) for i in BaseServingStatus]
    + [
        ("AD_GROUP_LOW_BID", "AD_GROUP_LOW_BID"),
        ("AD_GROUP_POLICING_PENDING_REVIEW", "AD_GROUP_POLICING_PENDING_REVIEW"),
        ("AD_GROUP_STATUS_ENABLED", "AD_GROUP_STATUS_ENABLED"),
        ("AD_GROUP_INCOMPLETE", "AD_GROUP_INCOMPLETE"),
        ("AD_GROUP_ARCHIVED", "AD_GROUP_ARCHIVED"),
        ("AD_GROUP_PAUSED", "AD_GROUP_PAUSED"),
        ("AD_GROUP_POLICING_CREATIVE_REJECTED", "AD_GROUP_POLICING_CREATIVE_REJECTED"),
    ],
)

ProductAdServingStatus = Enum(
    value="ProductAdServingStatus",
    names=[(i.name, i.value) for i in BaseServingStatus]
    + [
        ("AD_STATUS_LIVE", "AD_STATUS_LIVE"),
        ("AD_CREATION_OFFLINE_IN_PROGRESS", "AD_CREATION_OFFLINE_IN_PROGRESS"),
        ("AD_CREATION_OFFLINE_PENDING", "AD_CREATION_OFFLINE_PENDING"),
        ("AD_ELIGIBLE", "AD_ELIGIBLE"),
        ("AD_POLICING_PENDING_REVIEW", "AD_POLICING_PENDING_REVIEW"),
        ("ADVERTISER_ACCOUNT_OUT_OF_BUDGET", "ADVERTISER_ACCOUNT_OUT_OF_BUDGET"),
        ("ADVERTISER_EXCEED_SPENDS_LIMIT", "ADVERTISER_EXCEED_SPENDS_LIMIT"),
        ("ADVERTISER_STATUS_ENABLED", "ADVERTISER_STATUS_ENABLED"),
        ("CAMPAIGN_PENDING_START_DATE", "CAMPAIGN_PENDING_START_DATE"),
        ("ELIGIBLE", "ELIGIBLE"),
        ("SECURITY_SCAN_PENDING_REVIEW", "SECURITY_SCAN_PENDING_REVIEW"),
        ("ACCOUNT_OUT_OF_BUDGET", "ACCOUNT_OUT_OF_BUDGET"),
        ("AD_ARCHIVED", "AD_ARCHIVED"),
        ("AD_CREATION_FAILED", "AD_CREATION_FAILED"),
        ("AD_CREATION_OFFLINE_FAILED", "AD_CREATION_OFFLINE_FAILED"),
        ("AD_INELIGIBLE", "AD_INELIGIBLE"),
        ("AD_LANDING_PAGE_NOT_AVAILABLE", "AD_LANDING_PAGE_NOT_AVAILABLE"),
        ("AD_MISSING_DECORATION", "AD_MISSING_DECORATION"),
        ("AD_MISSING_IMAGE", "AD_MISSING_IMAGE"),
        ("AD_NO_PURCHASABLE_OFFER", "AD_NO_PURCHASABLE_OFFER"),
        ("AD_NOT_BUYABLE", "AD_NOT_BUYABLE"),
        ("AD_NOT_IN_BUYBOX", "AD_NOT_IN_BUYBOX"),
        ("AD_OUT_OF_STOCK", "AD_OUT_OF_STOCK"),
        ("AD_PAUSED", "AD_PAUSED"),
        ("AD_POLICING_SUSPENDED", "AD_POLICING_SUSPENDED"),
        ("CAMPAIGN_ADS_NOT_DELIVERING", "CAMPAIGN_ADS_NOT_DELIVERING"),
        ("CAMPAIGN_ENDED", "CAMPAIGN_ENDED"),
        ("INELIGIBLE", "INELIGIBLE"),
        ("LANDING_PAGE_NOT_AVAILABLE", "LANDING_PAGE_NOT_AVAILABLE"),
        ("MISSING_DECORATION", "MISSING_DECORATION"),
        ("MISSING_IMAGE", "MISSING_IMAGE"),
        ("NO_INVENTORY", "NO_INVENTORY"),
        ("NO_PURCHASABLE_OFFER", "NO_PURCHASABLE_OFFER"),
        ("NOT_BUYABLE", "NOT_BUYABLE"),
        ("NOT_IN_BUYBOX", "NOT_IN_BUYBOX"),
        ("OUT_OF_STOCK", "OUT_OF_STOCK"),
        ("PIR_RULE_EXCLUDED", "PIR_RULE_EXCLUDED"),
        ("SECURITY_SCAN_REJECTED", "SECURITY_SCAN_REJECTED"),
        ("STATUS_UNAVAILABLE", "STATUS_UNAVAILABLE"),
    ],
)
ProductAdServingStatus.__str__ = __str__

TargetServingStatus = Enum(
    value="TargetServingStatus",
    names=[(i.name, str(i.value)) for i in BaseServingStatus]
    + [
        ("TARGETING_CLAUSE_STATUS_LIVE", "TARGETING_CLAUSE_STATUS_LIVE"),
        ("TARGETING_CLAUSE_ARCHIVED", "TARGETING_CLAUSE_ARCHIVED"),
        ("TARGETING_CLAUSE_BLOCKED", "TARGETING_CLAUSE_BLOCKED"),
        ("TARGETING_CLAUSE_PAUSED", "TARGETING_CLAUSE_PAUSED"),
        ("TARGETING_CLAUSE_POLICING_SUSPENDED", "TARGETING_CLAUSE_POLICING_SUSPENDED"),
        ("ACCOUNT_OUT_OF_BUDGET", "ACCOUNT_OUT_OF_BUDGET"),
    ],
)
TargetServingStatus.__str__ = __str__

KeywordServingStatus = TargetServingStatus

BASE_VALID_SERVING_STATUSES = [
    BaseServingStatus.ADVERTISER_OUT_OF_BUDGET.value,
    BaseServingStatus.ADVERTISER_PAYMENT_FAILURE.value,
    BaseServingStatus.ADVERTISER_POLICING_PENDING_REVIEW.value,
    BaseServingStatus.CAMPAIGN_OUT_OF_BUDGET.value,
    BaseServingStatus.CAMPAIGN_STATUS_ENABLED.value,
    BaseServingStatus.PENDING_REVIEW.value,
    BaseServingStatus.PENDING_START_DATE.value,
    BaseServingStatus.PORTFOLIO_OUT_OF_BUDGET.value,
    BaseServingStatus.PORTFOLIO_PENDING_START_DATE.value,
    BaseServingStatus.PORTFOLIO_STATUS_ENABLED.value,
]

BASE_INVALID_SERVING_STATUSES = [
    BaseServingStatus.ADVERTISER_ARCHIVED.value,
    BaseServingStatus.ADVERTISER_PAUSED.value,
    BaseServingStatus.ADVERTISER_POLICING_SUSPENDED.value,
    BaseServingStatus.CAMPAIGN_ARCHIVED.value,
    BaseServingStatus.CAMPAIGN_INCOMPLETE.value,
    BaseServingStatus.CAMPAIGN_PAUSED.value,
    BaseServingStatus.ENDED.value,
    BaseServingStatus.OTHER.value,
    BaseServingStatus.PORTFOLIO_ARCHIVED.value,
    BaseServingStatus.PORTFOLIO_ENDED.value,
    BaseServingStatus.PORTFOLIO_PAUSED.value,
    BaseServingStatus.REJECTED.value,
]

TARGETS_VALID_STATUSES = [
    TargetServingStatus.TARGETING_CLAUSE_STATUS_LIVE.value,
    TargetServingStatus.ACCOUNT_OUT_OF_BUDGET.value,
] + BASE_VALID_SERVING_STATUSES

TARGETS_INVALID_STATUSES = [
    TargetServingStatus.TARGETING_CLAUSE_ARCHIVED.value,
    TargetServingStatus.TARGETING_CLAUSE_BLOCKED.value,
    TargetServingStatus.TARGETING_CLAUSE_PAUSED.value,
    TargetServingStatus.TARGETING_CLAUSE_POLICING_SUSPENDED.value,
] + BASE_INVALID_SERVING_STATUSES

KEYWORD_VALID_STATUSES = TARGETS_VALID_STATUSES
KEYWORD_INVALID_STATUSES = TARGETS_INVALID_STATUSES

CAMPAIGN_VALID_STATUSES = [
    CampaignServingStatus.CAMPAIGN_OUT_OF_BUDGET.value,
] + BASE_VALID_SERVING_STATUSES

CAMPAIGN_INVALID_STATUSES = BASE_INVALID_SERVING_STATUSES

AD_GROUP_VALID_STATUSES = [
    AdGroupServingStatus.AD_GROUP_LOW_BID.value,
    AdGroupServingStatus.AD_GROUP_POLICING_PENDING_REVIEW.value,
    AdGroupServingStatus.AD_GROUP_STATUS_ENABLED.value,
] + BASE_VALID_SERVING_STATUSES

AD_GROUP_INVALID_STATUSES = [
    AdGroupServingStatus.AD_GROUP_INCOMPLETE.value,
    AdGroupServingStatus.AD_GROUP_ARCHIVED.value,
    AdGroupServingStatus.AD_GROUP_PAUSED.value,
    AdGroupServingStatus.AD_GROUP_POLICING_CREATIVE_REJECTED.value,
] + BASE_INVALID_SERVING_STATUSES

PRODUCT_AD_VALID_STATUSES = [
    ProductAdServingStatus.AD_STATUS_LIVE.value,
    ProductAdServingStatus.AD_CREATION_OFFLINE_IN_PROGRESS.value,
    ProductAdServingStatus.AD_CREATION_OFFLINE_PENDING.value,
    ProductAdServingStatus.AD_POLICING_PENDING_REVIEW.value,
    ProductAdServingStatus.ADVERTISER_ACCOUNT_OUT_OF_BUDGET.value,
    ProductAdServingStatus.ADVERTISER_EXCEED_SPENDS_LIMIT.value,
    ProductAdServingStatus.ADVERTISER_STATUS_ENABLED.value,
    ProductAdServingStatus.CAMPAIGN_PENDING_START_DATE.value,
    ProductAdServingStatus.ELIGIBLE.value,
    ProductAdServingStatus.SECURITY_SCAN_PENDING_REVIEW.value,
    ProductAdServingStatus.ACCOUNT_OUT_OF_BUDGET.value,
] + BASE_VALID_SERVING_STATUSES

PRODUCT_AD_INVALID_STATUSES = [
    ProductAdServingStatus.AD_ARCHIVED.value,
    ProductAdServingStatus.AD_CREATION_FAILED.value,
    ProductAdServingStatus.AD_CREATION_OFFLINE_FAILED.value,
    ProductAdServingStatus.AD_INELIGIBLE.value,
    ProductAdServingStatus.AD_LANDING_PAGE_NOT_AVAILABLE.value,
    ProductAdServingStatus.AD_MISSING_DECORATION.value,
    ProductAdServingStatus.AD_MISSING_IMAGE.value,
    ProductAdServingStatus.AD_NO_PURCHASABLE_OFFER.value,
    ProductAdServingStatus.AD_NOT_BUYABLE.value,
    ProductAdServingStatus.AD_OUT_OF_STOCK.value,
    ProductAdServingStatus.AD_PAUSED.value,
    ProductAdServingStatus.AD_POLICING_SUSPENDED.value,
    ProductAdServingStatus.CAMPAIGN_ADS_NOT_DELIVERING.value,
    ProductAdServingStatus.CAMPAIGN_ENDED.value,
    ProductAdServingStatus.LANDING_PAGE_NOT_AVAILABLE.value,
    ProductAdServingStatus.MISSING_DECORATION.value,
    ProductAdServingStatus.MISSING_IMAGE.value,
    ProductAdServingStatus.NO_INVENTORY.value,
    ProductAdServingStatus.NOT_BUYABLE.value,
    ProductAdServingStatus.NOT_IN_BUYBOX.value,
    ProductAdServingStatus.OUT_OF_STOCK.value,
    ProductAdServingStatus.PIR_RULE_EXCLUDED.value,
    ProductAdServingStatus.SECURITY_SCAN_REJECTED.value,
    ProductAdServingStatus.STATUS_UNAVAILABLE.value,
] + BASE_INVALID_SERVING_STATUSES


class ServerLocation(str, Enum):
    NORTH_AMERICA = "NA"
    EUROPE = "EU"
    FAR_EAST = "FE"

    def __str__(self):
        return str(self.value)


MAX_CAMPAIGNS_BACH_SIZE = 100

MAX_AD_GROUPS_BACH_SIZE = 100


class SpState(str, Enum):
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"
    ENABLING = "ENABLING"
    USER_DELETED = "USER_DELETED"
    OTHER = "OTHER"

    def __str__(self):
        return str(self.value)


MAX_PRODUCT_ADS_BACH_SIZE = 1000


class AdProductTypes(str, Enum):
    SP_PRODUCTS = "SPONSORED_PRODUCTS"
    SP_BRANDS = "SPONSORED_BRANDS"

    def __str__(self):
        return str(self.value)


# Coutries for defining profiles
NA_COUNTRIES = ["US", "CA", "MX", "BR"]
EU_COUNTRIES = ["UK", "DE", "FR", "ES", "IT", "NL", "AE", "SE"]
FE_COUNTRIES = ["JP", "AU", "SG"]

REGIONS = {
    ServerLocation.NORTH_AMERICA: NA_COUNTRIES,
    ServerLocation.EUROPE: EU_COUNTRIES,
    ServerLocation.FAR_EAST: FE_COUNTRIES,
}

AuthURL = {
    ServerLocation.NORTH_AMERICA: "https://api.amazon.com/auth/o2/token",
    ServerLocation.EUROPE: "https://api.amazon.co.uk/auth/o2/token",
    ServerLocation.FAR_EAST: "https://api.amazon.co.jp/auth/o2/token",
}

BaseURL = {
    ServerLocation.NORTH_AMERICA: "https://advertising-api.amazon.com",
    ServerLocation.EUROPE: "https://advertising-api-eu.amazon.com",
    ServerLocation.FAR_EAST: "https://advertising-api-fe.amazon.com",
}

RefreshToken = {
    ServerLocation.NORTH_AMERICA: os.environ.get("ADS_API_REFRESH_TOKEN_US"),
    ServerLocation.EUROPE: os.environ.get("ADS_API_REFRESH_TOKEN_EU"),
    ServerLocation.FAR_EAST: os.environ.get("ADS_API_REFRESH_TOKEN_FE"),
}

DOMAINS = {
    "US": "com",
    "CA": "ca",
    "UK": "co.uk",
    "DE": "de",
    "ES": "es",
    "AU": "com.au",
    "IT": "it",
    "FR": "fr",
    "MX": "com.mx",
}

CURRENCIES = {
    "US": "USD",
    "CA": "EUR",
    "UK": "GBP",
    "DE": "EUR",
    "ES": "EUR",
    "AU": "AUD",
    "IT": "EUR",
    "FR": "EUR",
}

country_languages = {
    "US": "English",
    "CA": "English",
    "MX": "Spanish",
    "BR": "Portuguese",
    "UK": "English",
    "DE": "German",
    "FR": "French",
    "ES": "Spanish",
    "IT": "Italian",
    "NL": "Dutch",
    "AE": "Arabic",
    "SE": "Swedish",
    "JP": "Japanese",
    "AU": "English",
    "SG": "English",
}


class SpExpressionType(Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"
    OTHER = "OTHER"

    def __str__(self):
        return str(self.value)


class TargetingExpressionPredicateType(Enum):
    QUERY_BROAD_REL_MATCHES = "QUERY_BROAD_REL_MATCHES"
    QUERY_HIGH_REL_MATCHES = "QUERY_HIGH_REL_MATCHES"
    ASIN_ACCESSORY_RELATED = "ASIN_ACCESSORY_RELATED"
    ASIN_SUBSTITUTE_RELATED = "ASIN_SUBSTITUTE_RELATED"
    ASIN_CATEGORY_SAME_AS = "ASIN_CATEGORY_SAME_AS"
    ASIN_BRAND_SAME_AS = "ASIN_BRAND_SAME_AS"
    ASIN_PRICE_LESS_THAN = "ASIN_PRICE_LESS_THAN"
    ASIN_PRICE_BETWEEN = "ASIN_PRICE_BETWEEN"
    ASIN_PRICE_GREATER_THAN = "ASIN_PRICE_GREATER_THAN"
    ASIN_REVIEW_RATING_LESS_THAN = "ASIN_REVIEW_RATING_LESS_THAN"
    ASIN_REVIEW_RATING_BETWEEN = "ASIN_REVIEW_RATING_BETWEEN"
    ASIN_REVIEW_RATING_GREATER_THAN = "ASIN_REVIEW_RATING_GREATER_THAN"
    ASIN_SAME_AS = "ASIN_SAME_AS"
    ASIN_IS_PRIME_SHIPPING_ELIGIBLE = "ASIN_IS_PRIME_SHIPPING_ELIGIBLE"
    ASIN_AGE_RANGE_SAME_AS = "ASIN_AGE_RANGE_SAME_AS"
    ASIN_GENRE_SAME_AS = "ASIN_GENRE_SAME_AS"
    ASIN_EXPANDED_FROM = "ASIN_EXPANDED_FROM"
    OTHER = "OTHER"

    def __str__(self):
        return str(self.value)


class NegativeTargetingExpressionPredicateType(Enum):
    ASIN_BRAND_SAME_AS = "ASIN_BRAND_SAME_AS"
    ASIN_SAME_AS = "ASIN_SAME_AS"
    OTHER = "OTHER"

    def __str__(self):
        return str(self.value)


# placement report type is a custom type to run the placement report on the campaign reporting level
# search terms report type is a custom type to run the search terms report on the keyword reporting level
# all of these must be unique as they get stored in the ReportData model and allow filtering later
class SpReportType(str, Enum):
    CAMPAIGN = "campaigns"
    PLACEMENT = "placements"
    KEYWORD = "keywords"
    KEYWORD_QUERY = "keyword_query"  # AKA Search Term
    PRODUCT_AD = "productAds"
    TARGET = "targets"
    TARGET_QUERY = "target_query"

    def __str__(self):
        return str(self.value)


SP_REPORT_TYPES = [
    SpReportType.CAMPAIGN,
    SpReportType.PLACEMENT,
    SpReportType.KEYWORD,
    SpReportType.KEYWORD_QUERY,
    SpReportType.PRODUCT_AD,
    SpReportType.TARGET,
    SpReportType.TARGET_QUERY,
]


class BiddingStrategies(str, Enum):
    DOWN_ONLY = "LEGACY_FOR_SALES"
    UP_DOWN = "AUTO_FOR_SALES"
    FIXED_BIDS = "MANUAL"
    RULE_BASED = "RULE_BASED"

    def __str__(self):
        return str(self.value)


class SponsoredProductsPlacement(str, Enum):
    PLACEMENT_TOP = "PLACEMENT_TOP"
    PLACEMENT_PRODUCT_PAGE = "PLACEMENT_PRODUCT_PAGE"
    PLACEMENT_REST_OF_SEARCH = "PLACEMENT_REST_OF_SEARCH"

    def __str__(self):
        return str(self.value)


# Metrics which will be requested from Amazon for each report type. Mapped to SpReportType enum with a base set of
# metrics applicable to every report

# "Unsupported fields for other ASIN report: attributedSales30d,impressions,clicks,cost.",
# "State filter '[ENABLED]' is not supported for 'productAd' report.",
# "State filter '[ENABLED]' is not supported for 'otherAsin' report.",
# "State filter '[ENABLED]' is not supported for 'keyword' report with segment type 'query'.",
# "State filter '[ENABLED]' is not supported for 'targets' report with segment type 'query'.",
# "Segment '[PLACEMENT]' is not supported for 'targets' report for specified campaign type(s): 'sponsoredProducts'.",


# Auto search terms are given in the Query segment of the TARGET report which include keywords for Broad and Exact
# campaigns
class ReportStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    PROCESSING = "PROCESSING"
    INTERNAL_PROCESSED = "INTERNAL_PROCESSED"
    EMPTY = "EMPTY"
    FAILURE = "FAILED"
    INTERNAL_FAILURE = "INTERNAL_FAILURE"

    def __str__(self):
        return str(self.value)


class AmazonReportStatuses(tuple, Enum):
    PENDING: tuple = ReportStatus.PENDING, ReportStatus.PROCESSING
    COMPLETED: tuple = ReportStatus.COMPLETED
    FAILURE: tuple = ReportStatus.FAILURE


class InitialReportStatuses(tuple, Enum):
    COMPLETED: tuple = ReportStatus.INTERNAL_PROCESSED
    EMPTY: tuple = ReportStatus.EMPTY
    FAILURE: tuple = ReportStatus.INTERNAL_FAILURE


class TypeIdOfReport(str, Enum):
    SP_TARGETING = "spTargeting"
    SP_SEARCH_TERM = "spSearchTerm"
    SP_CAMPAIGNS = "spCampaigns"
    SP_ADVERTISED_PRODUCT = "spAdvertisedProduct"
    SP_PURCHASED_PRODUCT = "spPurchasedProduct"
    SB_PURCHASED_PRODUCT = "sbPurchasedProduct"

    def __str__(self):
        return str(self.value)


class FormatOfReport(str, Enum):
    GZIP_JSON = "GZIP_JSON"

    def __str__(self):
        return str(self.value)


class TimeUnitOfReport(str, Enum):
    SUMMARY = "SUMMARY"
    DAILY = "DAILY"

    def __str__(self):
        return str(self.value)


DEFAULT_REQUESTED_DATE_RANGE_FOR_REPORTS = 14


class PlacementsOnAmazon(str, Enum):
    TOS = "Top of Search on-Amazon"
    PP = "Detail Page on-Amazon"
    OTHER = "Other on-Amazon"

    def __str__(self):
        return str(self.value)


class AdStatus(str, Enum):
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"

    def __str__(self):
        return str(self.value)


VARIABLE_KEYWORD_FIELDS = {
    "state": "state",
    "bid": "bid",
    "servingStatus": "serving_status",
    "lastUpdatedDate": "last_updated_date_on_amazon",
}

PURPOSE_BOOK_MODEL_MAP = {
    "Auto-Discovery": "campaign_discovery",
    "Broad-Research": "campaign_research_kw",
    "Broad-Research-Single": "campaign_research_single_kw",
    "Cat-Research": "campaign_research_cat",
    "Exact-Scale": "campaign_scale_kw",
    "Exact-Scale-Single": "campaign_scale_single_kw",
    "Product-Comp": "campaign_scale_asin",
    "GP": "campaign_gp",
}

BOOK_FORMATS_MAP = {
    "Unknown Binding": "Paperback",
    # German
    "Taschenbuch": "Paperback",
    "Gebundene Ausgabe": "Hardcover",
    # Spanish
    "Tapa blanda": "Paperback",
    "Tapa dura": "Hardcover",
    # French
    "Broché": "Paperback",
    "Relié": "Hardcover",
    # Italian
    "Copertina flessibile": "Paperback",
    "Copertina rigida": "Hardcover",
}


class SpEndpoint(str, Enum):
    CAMPAIGNS = "/v2/sp/campaigns"
    AD_GROUPS = "/v2/sp/adGroups"
    KEYWORDS = "/v2/sp/keywords"
    NEGATIVE_KEYWORDS = "/v2/sp/negativeKeywords"
    CAMPAIGN_NEGATIVE_KEYWORDS = "/v2/sp/campaignNegativeKeywords"
    PRODUCT_ADS = "/v2/sp/productAds"
    TARGETS = "/v2/sp/targets"
    NEGATIVE_TARGETS = "/v2/sp/negativeTargets"
    KEYWORD_BID_RECOMMENDATIONS = "/v2/sp/keywords/bidRecommendations"
    TARGET_BID_RECOMMENDATIONS = "/v2/sp/targets/bidRecommendations"


NEGATIVE_ENDPOINTS = [
    SpEndpoint.NEGATIVE_KEYWORDS,
    SpEndpoint.CAMPAIGN_NEGATIVE_KEYWORDS,
    SpEndpoint.NEGATIVE_TARGETS,
]

KEYWORD_ENDPOINTS = [
    SpEndpoint.KEYWORDS,
    SpEndpoint.NEGATIVE_KEYWORDS,
    SpEndpoint.CAMPAIGN_NEGATIVE_KEYWORDS,
]

CAMPAIGN_MAX_TARGETS_MAP = {
    "Auto-Discovery": 999,
    "Broad-Research": 30,
    "Cat-Research": 10,
    "Exact-Scale": 15,
    "Product-Comp": 30,
    "Product-Own": 30,
    "Product-Exp": 30,
    "Product-Self": 999,
    "GP": 1000,
}

CAMPAIGN_PURPOSE_TYPES = {
    "Keyword": [
        "Broad-Research",
        "Broad-Research-Single",
        "Exact-Scale",
        "Exact-Scale-Single",
        "GP",
    ],
    "Product": ["Auto-Discovery", "Cat-Research", "Product-Comp"],
}


class BookData(NamedTuple):
    """Helper class to aggregate book asin, price and be_acos information"""

    asin: str
    price: float
    be_acos: float
    reviews: int


class SlicePerformance(NamedTuple):
    """Helper class to aggregate keyword, target, placement performance chunks"""

    total_sales: float
    acos: float
    cpc: float


class QueryData(NamedTuple):
    """Helper class to allow looping through keyword queries (Search terms) and targets (ASINs)"""

    query_report: SpReportType
    keyword_report: SpReportType
    pos_endpoint: SpEndpoint
    neg_endpoint: SpEndpoint


QUERY_TYPES = [
    QueryData(
        SpReportType.KEYWORD_QUERY,
        SpReportType.KEYWORD,
        SpEndpoint.KEYWORDS,
        SpEndpoint.NEGATIVE_KEYWORDS,
    ),
    QueryData(
        SpReportType.TARGET_QUERY,
        SpReportType.TARGET,
        SpEndpoint.TARGETS,
        SpEndpoint.NEGATIVE_TARGETS,
    ),
]

# Ref: https://kdp.amazon.com/en_US/help/topic/G201645450
EU_VAT_PERCENTAGES = {
    "DE": 0.07,
    "FR": 0.055,
    "IT": 0.04,
    "ES": 0.04,
    "NL": 0.09,
}

TIME_LIMITS = {
    "AU": 12,
    "DE": 22,
    "ES": 22,
    "FR": 22,
    "IT": 22,
}

MAX_SHORT_BOOK_LENGTH = 110


RATES = {
    # https://kdp.amazon.com/en_US/help/topic/G201834340
    "Paperback": {  # format
        "Black": {  # colour print
            "Short": {  # book length
                "Regular": {  # trim size
                    "Fixed": {  # cost type
                        "US": 2.30,
                        "CA": 2.99,
                        "UK": 1.93,
                        "DE": 2.05,
                        "FR": 2.05,
                        "IT": 2.05,
                        "ES": 2.05,
                        "NL": 2.05,
                        "AU": 4.74,
                        "JP": 422,
                        "PL": 9.58,
                        "SE": 22.84,
                    },
                },
                "Large": {
                    "Fixed": {
                        "US": 2.84,
                        "CA": 3.53,
                        "UK": 2.15,
                        "DE": 2.48,
                        "FR": 2.48,
                        "IT": 2.48,
                        "ES": 2.48,
                        "NL": 2.48,
                        "AU": 5.28,
                        "JP": 530,
                        "PL": 11.61,
                        "SE": 27.67,
                    },
                },
            },
            "Long": {
                "Regular": {
                    "Fixed": {
                        "US": 1,
                        "CA": 1.26,
                        "UK": 0.85,
                        "DE": 0.75,
                        "FR": 0.75,
                        "IT": 0.75,
                        "ES": 0.75,
                        "NL": 0.75,
                        "AU": 2.42,
                        "JP": 206,
                        "PL": 3.51,
                        "SE": 8.37,
                    },
                    "Per_Page": {
                        "US": 0.012,
                        "CA": 0.016,
                        "UK": 0.010,
                        "DE": 0.012,
                        "FR": 0.012,
                        "IT": 0.012,
                        "ES": 0.012,
                        "NL": 0.012,
                        "AU": 0.022,
                        "JP": 2,
                        "PL": 0.056,
                        "SE": 0.134,
                    },
                },
                "Large": {
                    "Fixed": {
                        "US": 1,
                        "CA": 1.26,
                        "UK": 0.85,
                        "DE": 0.75,
                        "FR": 0.75,
                        "IT": 0.75,
                        "ES": 0.75,
                        "NL": 0.75,
                        "AU": 2.42,
                        "JP": 206,
                        "PL": 3.51,
                        "SE": 8.37,
                    },
                    "Per_Page": {
                        "US": 0.017,
                        "CA": 0.021,
                        "UK": 0.012,
                        "DE": 0.016,
                        "FR": 0.016,
                        "IT": 0.016,
                        "ES": 0.016,
                        "NL": 0.016,
                        "AU": 0.027,
                        "JP": 3,
                        "PL": 0.075,
                        "SE": 0.179,
                    },
                },
            },
        },
        "Colour": {
            "Short": {
                "Regular": {
                    "Fixed": {
                        "US": 3.60,
                        "CA": 4.66,
                        "UK": 2.65,
                        "DE": 3.03,
                        "FR": 3.03,
                        "IT": 3.03,
                        "ES": 3.03,
                        "NL": 3.03,
                        "AU": 5.82,
                        "JP": 475,
                        "PL": 12.86,
                        "SE": 30.65,
                    },
                },
                "Large": {
                    "Fixed": {
                        "US": 4.20,
                        "CA": 5.26,
                        "UK": 3.25,
                        "DE": 3.63,
                        "FR": 3.63,
                        "IT": 3.63,
                        "ES": 3.63,
                        "NL": 3.63,
                        "AU": 6.42,
                        "JP": 475,
                        "PL": 15.32,
                        "SE": 36.51,
                    },
                },
            },
            "Long": {
                "Regular": {
                    "Fixed": {
                        "US": 1,
                        "CA": 1.26,
                        "UK": 0.85,
                        "DE": 0.75,
                        "FR": 0.75,
                        "IT": 0.75,
                        "ES": 0.75,
                        "NL": 0.75,
                        "AU": 2.42,
                        "JP": 206,
                        "PL": 3.51,
                        "SE": 8.37,
                    },
                    "Per_Page": {
                        "US": 0.065,
                        "CA": 0.085,
                        "UK": 0.045,
                        "DE": 0.057,
                        "FR": 0.057,
                        "IT": 0.057,
                        "ES": 0.057,
                        "NL": 0.057,
                        "AU": 0.085,
                        "JP": 4,
                        "PL": 0.267,
                        "SE": 0.636,
                    },
                },
                "Large": {
                    "Fixed": {
                        "US": 1,
                        "CA": 1.26,
                        "UK": 0.85,
                        "DE": 0.75,
                        "FR": 0.75,
                        "IT": 0.75,
                        "ES": 0.75,
                        "NL": 0.75,
                        "AU": 2.42,
                        "JP": 206,
                        "PL": 3.51,
                        "SE": 8.37,
                    },
                    "Per_Page": {
                        "US": 0.08,
                        "CA": 0.010,
                        "UK": 0.06,
                        "DE": 0.072,
                        "FR": 0.072,
                        "IT": 0.072,
                        "ES": 0.072,
                        "NL": 0.072,
                        "AU": 0.010,
                        "JP": 5,
                        "PL": 0.072,
                        "SE": 0.804,
                    },
                },
            },
        },
    },
    # https://kdp.amazon.com/en_US/help/topic/GHT976ZKSKUXBB6H
    "Hardcover": {
        "Black": {
            "Short": {
                "Regular": {
                    "Fixed": {
                        "US": 6.80,
                        "CA": 6.80,
                        "UK": 5.23,
                        "DE": 5.95,
                        "FR": 5.95,
                        "IT": 5.95,
                        "ES": 5.95,
                        "NL": 5.95,
                        "PL": 27.85,
                        "SE": 66.38,
                    },
                },
                "Large": {
                    "Fixed": {
                        "US": 7.49,
                        "CA": 7.49,
                        "UK": 5.45,
                        "DE": 6.35,
                        "FR": 6.35,
                        "IT": 6.35,
                        "ES": 6.35,
                        "NL": 6.35,
                        "PL": 29.87,
                        "SE": 71.21,
                    },
                },
            },
            "Long": {
                "Regular": {
                    "Fixed": {
                        "US": 5.65,
                        "CA": 5.65,
                        "UK": 4.15,
                        "DE": 4.65,
                        "FR": 4.65,
                        "IT": 4.65,
                        "ES": 4.65,
                        "NL": 4.65,
                        "PL": 20.34,
                        "SE": 48.49,
                    },
                    "Per_Page": {
                        "US": 0.012,
                        "CA": 0.012,
                        "UK": 0.010,
                        "DE": 0.012,
                        "FR": 0.012,
                        "IT": 0.012,
                        "ES": 0.012,
                        "NL": 0.012,
                        "PL": 0.056,
                        "SE": 0.134,
                    },
                },
                "Large": {
                    "Fixed": {
                        "US": 5.65,
                        "CA": 5.65,
                        "UK": 4.15,
                        "DE": 4.65,
                        "FR": 4.65,
                        "IT": 4.65,
                        "ES": 4.65,
                        "NL": 4.65,
                        "PL": 20.34,
                        "SE": 48.49,
                    },
                    "Per_Page": {
                        "US": 0.017,
                        "CA": 0.017,
                        "UK": 0.012,
                        "DE": 0.016,
                        "FR": 0.016,
                        "IT": 0.016,
                        "ES": 0.016,
                        "NL": 0.016,
                        "PL": 0.075,
                        "SE": 0.179,
                    },
                },
            },
        },
        "Colour": {
            "Regular": {
                "Fixed": {
                    "US": 5.65,
                    "CA": 5.65,
                    "UK": 4.15,
                    "DE": 4.65,
                    "FR": 4.65,
                    "IT": 4.65,
                    "ES": 4.65,
                    "NL": 4.65,
                    "PL": 21.78,
                    "SE": 51.91,
                },
                "Per_Page": {
                    "US": 0.065,
                    "CA": 0.065,
                    "UK": 0.045,
                    "DE": 0.057,
                    "FR": 0.057,
                    "IT": 0.057,
                    "ES": 0.057,
                    "NL": 0.057,
                    "PL": 0.267,
                    "SE": 0.636,
                },
            },
            "Large": {
                "Fixed": {
                    "US": 5.65,
                    "CA": 5.65,
                    "UK": 4.15,
                    "DE": 4.65,
                    "FR": 4.65,
                    "IT": 4.65,
                    "ES": 4.65,
                    "NL": 4.65,
                    "PL": 21.78,
                    "SE": 51.91,
                },
                "Per_Page": {
                    "US": 0.080,
                    "CA": 0.080,
                    "UK": 0.060,
                    "DE": 0.072,
                    "FR": 0.072,
                    "IT": 0.072,
                    "ES": 0.072,
                    "NL": 0.072,
                    "PL": 0.337,
                    "SE": 0.084,
                },
            },
        },
    },
    # Ref: https://kdp.amazon.com/en_US/help/topic/G200634560
    "Kindle": {
        "higher_royalty_threshold": {
            "US": 2.99,
            "CA": 2.99,
            "BR": 5.99,
            "UK": 1.77,
            "DE": 2.51,
            "FR": 2.55,
            "IT": 2.20,
            "ES": 2.59,
            "NL": 2.47,
            "JP": 250,
            "MX": 34.99,
            "AU": 3.99,
            "IN": 99,
        },
        # per MB
        "Delivery": {
            "US": 0.15,
            "CA": 0.15,
            "BR": 0.30,
            "UK": 0.10,
            "DE": 0.12,
            "FR": 0.12,
            "ES": 0.12,
            "IT": 0.12,
            "NL": 0.12,
            "JP": 1,
            "MX": 1,
            "AU": 0.15,
            "IN": 7,
        },
    },
}


SCRAPE_OPS_PROXY_LOCATIONS = [
    "br",
    "ca",
    "cn",
    "in",
    "it",
    "jp",
    "fr",
    "de",
    "ru",
    "es",
    "us",
    "uk",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Mozilla/5.0 (X11; Linux i686; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12.6; rv:106.0) Gecko/20100101 Firefox/106.0",
]

HEADERS_LIST = [
    # Firefox 77 Mac
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
    # Firefox 77 Windows
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
    # Chrome 83 Mac
    {
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    },
    # Chrome 83 Windows
    {
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
    },
]

TOP_50_COMMON_KEYWORDS = [
    "the",
    "of",
    "and",
    "to",
    "a",
    "in",
    "that",
    "it",
    "with",
    "as",
    "for",
    "was",
    "on",
    "are",
    "by",
    "be",
    "at",
    "this",
    "an",
    "which",
    "or",
    "from",
    "not",
    "but",
    "what",
    "all",
    "were",
    "when",
    "we",
    "there",
    "can",
    "an",
    "your",
    "said",
    "each",
    "how",
    "their",
    "if",
    "will",
    "up",
    "other",
    "about",
    "out",
    "many",
    "then",
    "them",
    "these",
    "so",
    "some",
    "her",
    "would",
    "make",
    "like",
    "him",
    "into",
    "time",
    "has",
    "look",
    "two",
    "more",
    "write",
    "go",
    "see",
    "number",
    "no",
    "way",
    "could",
    "people",
    "book",
    "books",
    "kindle",
    "amazon",
]

# without AU
BOOKS_BEAM_MARKETPLACES_IDS = {
    "CA": 12,
    "MX": 11,
    "ES": 6,
    "FR": 7,
    "IT": 9,
    "DE": 4,
    "UK": 2,
    "US": 1,
}

CAMPAIGN_TYPES_REQUIRED_TARGETS = [
    "Broad-Research",
    "Broad-Research-Single",
    "Exact-Scale",
    "Exact-Scale-Single",
    "Product-Comp",
    "Product-Own",
    "Product-Exp",
    "GP"
]


class TimeUnit(Enum):
    SECOND = "SECOND"
    MILLISECOND = "MILLISECOND"

    def __str__(self):
        return str(self.value)
