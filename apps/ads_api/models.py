from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.ads_api.constants import (
    DEFAULT_BID,
    DEFAULT_BOOK_LENGTH,
    DEFAULT_BOOK_PRICE,
    DEFAULT_EBOOK_PRICE,
    DEFAULT_BE_ACOS,
    DEFAULT_BE_ACOS_KINDLE,
    AdGroupServingStatus,
    BiddingStrategies,
    CampaignServingStatus,
    MatchType,
    NegativeMatchType,
    ProductAdServingStatus,
    ReportStatus,
    ServerLocation,
    SpExpressionType,
    SpState,
)
from apps.utils.models import BaseModel

STATE_CHOICES = [
    (SpState.ENABLED.value, "Enabled"),
    (SpState.PAUSED.value, "Paused"),
    (SpState.ARCHIVED.value, "Archived"),
    (SpState.ENABLING.value, "Enabling"),
    (SpState.OTHER.value, "Other"),
]

MATCH_TYPE_CHOICES = [
    (MatchType.EXACT.value, "Exact"),
    (MatchType.PHRASE.value, "Phrase"),
    (MatchType.BROAD.value, "Broad"),
    (NegativeMatchType.EXACT.value, "Negative Exact"),
    (NegativeMatchType.PHRASE.value, "Negative Phrase"),
    (NegativeMatchType.BROAD.value, "Negative Broad"),
    (MatchType.OTHER.value, "Other"),
]

TARGET_SERVING_STATUS_CHOICES = [
    ("TARGETING_CLAUSE_ARCHIVED", "Target Archived"),
    ("TARGETING_CLAUSE_PAUSED", "Target Paused"),
    ("TARGETING_CLAUSE_STATUS_LIVE", "Target Enabled"),
    ("TARGETING_CLAUSE_POLICING_SUSPENDED", "Targed Suspended"),
    ("CAMPAIGN_OUT_OF_BUDGET", "Campaign Budget Limited"),
    ("AD_GROUP_PAUSED", "Ad Group Paused"),
    ("AD_GROUP_ARCHIVED", "Ad Group Archived"),
    ("CAMPAIGN_PAUSED", "Campaign Paused"),
    ("CAMPAIGN_ARCHIVED", "Campaign Archived"),
    ("ACCOUNT_OUT_OF_BUDGET", "Account Budget Limited"),
    ("PENDING_START_DATE", "Pending Start Data"),
]

AD_GROUP_SERVING_STATUS_CHOICES = [
    ("AD_GROUP_ARCHIVED", "Ad Group Archived"),
    ("AD_GROUP_PAUSED", "Ad Group Paused"),
    ("AD_GROUP_STATUS_ENABLED", "Ad Group Enabled"),
    ("AD_POLICING_SUSPENDED", "Ad Suspended"),
    ("AD_GROUP_INCOMPLETE", "Ad Group Incomplete"),
    ("CAMPAIGN_OUT_OF_BUDGET", "Campaign Budget Limited"),
    ("CAMPAIGN_PAUSED", "Campaign Paused"),
    ("CAMPAIGN_ARCHIVED", "Campaign Archived"),
    ("CAMPAIGN_INCOMPLETE", "Campaign Incomplete"),
    ("ACCOUNT_OUT_OF_BUDGET", "Account Budget Limited"),
    ("PENDING_START_DATE", "Pending Start Data"),
]

TARGETING_TYPE_CHOICES = [
    (SpExpressionType.MANUAL.value, "Manual"),
    (SpExpressionType.AUTO.value, "Auto"),
    (SpExpressionType.OTHER.value, "Other"),
]

MANUAL_TYPE_CHOICES = [
    ("Product", "Product"),
    ("Keyword", "Keyword"),
]


# updated as outlined here: https://stackoverflow.com/a/60918042/7568146
# official write up: https://docs.djangoproject.com/en/4.0/ref/models/fields/#enumeration-types
# decoupled from Django to use Enums
class MarketplaceIdChoice(models.TextChoices):
    US = "ATVPDKIKX0DER", "US"
    CA = "A2EUQ1WTGCTBG2", "CA"
    MX = "A1AM78C64UM0Y8", "MX"
    UK = "A1F83G8C2ARO7P", "UK"
    AU = "A39IBJ37TRP1C6", "AU"
    DE = "A1PA6795UKMFR9", "DE"
    ES = "A1RKKUPIHCS9HS", "ES"
    FR = "A13V1IB3VIYZZH", "FR"
    IT = "APJ6JRA9NG5V4", "IT"


class CountryCodeChoice(models.TextChoices):
    US = "US"
    CA = "CA"
    MX = "MX"
    UK = "UK"
    AU = "AU"
    DE = "DE"
    ES = "ES"
    FR = "FR"
    IT = "IT"


class CampaignPurpose(models.TextChoices):
    Discovery = "Auto-Discovery", "Auto-Discovery"
    Discovery_Loose_Match = "Auto-Discovery-Loose-Match", "Auto-Discovery-Loose-Match"
    Discovery_Close_Match = "Auto-Discovery-Close-Match", "Auto-Discovery-Close-Match"
    Discovery_Substitutes = "Auto-Discovery-Substitutes", "Auto-Discovery-Substitutes"
    Discovery_Complements = "Auto-Discovery-Complements", "Auto-Discovery-Complements"

    Cat_Research = "Cat-Research", "Cat-Research"
    Broad_Research = "Broad-Research", "Broad-Research"
    Broad_Research_Single = "Broad-Research-Single", "Broad-Research-Single"
    Exact_Scale = "Exact-Scale", "Exact-Scale"
    Exact_Scale_Single = "Exact-Scale-Single", "Exact-Scale-Single"
    Product_Comp = "Product-Comp", "Product-Comp"
    Product_Own = "Product-Own", "Product-Own"
    Product_Self = "Product-Self", "Product-Self"
    Product_Exp = "Product-Exp", "Product-Exp"
    GP = "GP", "GP"
    Auto_GP = "Auto-GP", "Auto-GP"


# TODO: Add a Client model to house the payment information. Associate multiple Profiles with a Client as may be necessary to do with vanity publishers


class Profile(BaseModel):
    """
    Profiles of all users the client has access to in the NA region
    """

    PROFILE_TYPE_CHOICES = [
        ("vendor", "Vendor"),
        ("seller", "Seller"),
    ]

    profile_id = models.PositiveBigIntegerField(unique=True, db_index=True)
    country_code = models.CharField(
        max_length=99, choices=CountryCodeChoice.choices, default=CountryCodeChoice.US
    )
    marketplace_string_id = models.CharField(
        max_length=99,
        choices=MarketplaceIdChoice.choices,
        default=MarketplaceIdChoice.US,
    )
    entity_id = models.CharField(max_length=99)  # aka account_id
    valid_payment_method = models.BooleanField(default=False)
    nickname = models.CharField(max_length=99, default="")
    monthly_budget = models.PositiveIntegerField(blank=True, null=True, default=999999)
    managed = models.BooleanField(default=False)
    research_percentage = models.PositiveIntegerField(default=20)
    profit_mode = models.BooleanField(default=False)
    profile_server = models.CharField(max_length=99, default=ServerLocation.NORTH_AMERICA)
    accessible = models.BooleanField(default=True)
    type = models.CharField(
        max_length=10,
        choices=PROFILE_TYPE_CHOICES,
        default="vendor",
    )
    surplus_budget = models.PositiveIntegerField(default=0, editable=False)

    def __str__(self):
        return f"{self.nickname} [{self.country_code}]"

    def save(self, *args, **kwargs):
        from apps.ads_api.services.books.update_managed_books_for_unmanaged_profiles import (
            UpdateManagedBooksForUnmanagedProfilesService,
        )
        from apps.ads_api.services.campaigns.update_managed_campaigns_for_unmanaged_profiles import (
            UpdateManagedCampaignsForUnmanagedProfilesService,
        )

        creating = self._state.adding
        if not creating:
            old_managed = Profile.objects.get(pk=self.pk).managed
            if old_managed != self.managed and self.managed == False:
                UpdateManagedBooksForUnmanagedProfilesService.update([self.pk])
                UpdateManagedCampaignsForUnmanagedProfilesService.update([self.pk])

        super().save(*args, **kwargs)


class Campaign(BaseModel):
    """
    High level campaigns information
    """

    # Limiting choices
    SPONSORING_CHOICES = [
        ("sponsoredProducts", "SP"),
        ("sponsoredBrands", "SB"),
    ]

    BIDDING_STRATEGY_CHOICES = [
        (BiddingStrategies.DOWN_ONLY.value, "Down Only"),
        (BiddingStrategies.UP_DOWN.value, "Up & Down"),
        (BiddingStrategies.FIXED_BIDS.value, "Fixed Bids"),
    ]

    # Data reported by Amazon API - purely informational
    campaign_id_amazon = models.PositiveBigIntegerField(
        unique=True, db_index=True
    )  # Note: could use unique=True, db_index=True
    brand_campaign_id = models.CharField(max_length=99, default="", null=True, blank=True)
    profile = models.ForeignKey(
        "Profile",
        verbose_name=("Profile"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="campaigns",
    )
    portfolio_id = models.PositiveBigIntegerField(
        null=True, blank=True
    )  # Each profile contains >0 campaigns and >=0 portfolios, some campaigns *may be* in portfolios but not necessarily,
    sponsoring_type = models.CharField(max_length=99, choices=SPONSORING_CHOICES, default="sponsoredProducts")
    targeting_type = models.CharField(
        max_length=99,
        choices=TARGETING_TYPE_CHOICES,
        default=SpExpressionType.MANUAL.value,
    )
    serving_status = models.CharField(
        max_length=99,
        choices=[(i.name, i.value) for i in CampaignServingStatus],
        default=CampaignServingStatus.CAMPAIGN_STATUS_ENABLED.value,
        null=True,
    )
    last_updated_date_on_amazon = models.PositiveBigIntegerField(default=0, null=True)  # in epoch time

    # Input data which may be edited externally (outside of the app and frontend UI) and internally so needs to be updated via GET request to Amazon API
    campaign_name = models.CharField(max_length=254, default="")
    state = models.CharField(max_length=99, choices=STATE_CHOICES, default=SpState.ENABLED.value)
    placement_tos_mult = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(900), MinValueValidator(0)]
    )
    placement_pp_mult = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(900), MinValueValidator(0)]
    )
    bidding_strategy = models.CharField(
        max_length=99,
        choices=BIDDING_STRATEGY_CHOICES,
        default=BiddingStrategies.DOWN_ONLY.value,
    )
    daily_budget = models.DecimalField(default=Decimal("20.01"), max_digits=12, decimal_places=2)
    premium_bid_adjustment = models.BooleanField(default=False)

    # Input data unique to the app
    managed = models.BooleanField(default=False)
    target_acos = models.DecimalField(max_digits=8, decimal_places=2, default=0, null=True)
    asins = ArrayField(models.CharField(max_length=99, blank=True), default=list)
    campaign_purpose = models.CharField(max_length=99, choices=CampaignPurpose.choices, default="", null=True)
    manual_type = models.CharField(
        max_length=99, choices=MANUAL_TYPE_CHOICES, default="", null=True
    )  # only applies to manual targeting_type
    creation_retries_count = models.IntegerField(default=0)

    def __str__(self):
        return self.campaign_name


class AdGroup(BaseModel):
    """
    High level ad group information
    """

    campaign = models.ForeignKey(
        "Campaign",
        verbose_name=("Campaign"),
        on_delete=models.CASCADE,
        related_name="ad_groups",
    )
    ad_group_id = models.PositiveBigIntegerField(db_index=True)
    brand_ad_group_id = models.CharField(max_length=99, default="", null=True, blank=True)
    ad_group_name = models.CharField(max_length=254, default="")
    state = models.CharField(max_length=99, choices=STATE_CHOICES, default=SpState.ENABLED.value, null=True)
    serving_status = models.CharField(
        max_length=99,
        choices=[(i.name, i.value) for i in AdGroupServingStatus],
        default=AdGroupServingStatus.AD_GROUP_STATUS_ENABLED.name,
        null=True,
    )
    last_updated_date_on_amazon = models.PositiveBigIntegerField(default=0, null=True)
    manual_type = models.CharField(max_length=99, choices=MANUAL_TYPE_CHOICES, default="", null=True)
    default_bid = models.DecimalField(max_digits=8, decimal_places=2, default=DEFAULT_BID, null=True)

    class Meta:
        constraints = (models.UniqueConstraint(fields=("ad_group_id", "campaign"), name="unique_ad_group"),)

    def __str__(self):
        return self.ad_group_name


class ProductAd(BaseModel):
    """
    High level product ad information
    """

    campaign = models.ForeignKey(
        "Campaign",
        verbose_name=("Campaign"),
        on_delete=models.CASCADE,
        related_name="product_ads",
    )
    ad_group = models.ForeignKey("AdGroup", verbose_name=("Ad Group"), on_delete=models.CASCADE)
    product_ad_id = models.PositiveBigIntegerField()
    state = models.CharField(max_length=99, choices=STATE_CHOICES, default=SpState.ENABLED.value, null=True)
    asin = models.CharField(max_length=99, default="", null=True)
    last_updated_date_on_amazon = models.PositiveBigIntegerField(default=0, null=True)
    serving_status = models.CharField(
        max_length=99,
        choices=[(i.name, i.value) for i in ProductAdServingStatus],
        default="",
        null=True,
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("product_ad_id", "campaign", "ad_group"), name="unique_product_ad"
            ),
        )

    def __str__(self):
        return f"{self.asin} in Ad Group: {self.ad_group}"


class ReportData(BaseModel):
    """
    Granular individual data at various levels, available on a "day" timescale resolution
    Data is available for the last 60 days
    Data will be pulled via Amazon API daily for 10 days ago to 2 days ago, ignoring today's and yesterday's data
    """

    def __str__(self):
        return f"{self.report_type} report dated: {self.date} on profile: {self.campaign.profile.nickname} [{self.campaign.profile.country_code}]"

    # Unique identification data - required for all entries
    campaign = models.ForeignKey(
        "Campaign", verbose_name=("CampaignKey"), on_delete=models.SET_NULL, null=True
    )
    date = models.DateField(null=True)
    report_type = models.CharField(max_length=99, default="")  # SpReportType

    # Baseline data - obtained from SP report
    impressions = models.PositiveIntegerField(default=0, null=True)
    clicks = models.PositiveIntegerField(default=0, null=True)
    spend = models.DecimalField(max_digits=8, decimal_places=2, default=0, null=True)
    sales = models.DecimalField(max_digits=8, decimal_places=2, default=0, null=True)  # attributedSales30d
    orders = models.PositiveIntegerField(default=0, null=True)  # attributedUnitsOrdered30d
    kenp_royalties = models.PositiveIntegerField(
        default=0, null=True
    )  # attributedKindleEditionNormalizedPagesRoyalties14d

    # Obtained from campaign placement report
    placement = models.CharField(
        max_length=254, default=""
    )  # Could be: Top of Search on-Amazon    Detail Page on-Amazon    Other on-Amazon

    # Additional report data - obtained from other reports
    top_of_search_impression_share = models.DecimalField(max_digits=8, decimal_places=2, default=0, null=True)
    ad_id = models.PositiveBigIntegerField(null=True)
    ad_group_id = models.PositiveBigIntegerField(null=True)
    ad_group_name = models.CharField(max_length=254, default="")
    keyword_id = models.PositiveBigIntegerField(null=True)
    keyword_text = models.CharField(max_length=254, default="")
    query = models.CharField(max_length=254, default="")
    match_type = models.CharField(
        max_length=99, default=""
    )  # Type of matching for the keyword or phrase used in bid. Must be one of: BROAD, PHRASE, or EXACT
    asin = models.CharField(max_length=99, default="")
    target_id = models.PositiveBigIntegerField(null=True)
    target_expression = models.CharField(max_length=254, default="")
    target_text = models.CharField(max_length=254, default="")
    target_type = models.CharField(max_length=99, default="")
    units_sold_14d = models.PositiveIntegerField(default=0, null=True)
    attributed_conversions_30d = models.PositiveIntegerField(default=0, null=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=(
                    "ad_id",
                    "keyword_id",
                    "target_id",
                    "asin",
                    "query",
                    "placement",
                    "campaign",
                    "date",
                    "report_type",
                ),
                name="unique_report_data",
            ),
        )


class RecentReportData(BaseModel):
    """Model for storing report data for the last 90 days. Should have the same fields as ReportData"""

    """
    Granular individual data at various levels, available on a "day" timescale resolution
    Data is available for the last 90 days
    Data will be pulled via Amazon API daily for 10 days ago to 2 days ago, ignoring today's and yesterday's data
    """

    def __str__(self):
        return f"{self.report_type} report dated: {self.date} on profile: {self.campaign.profile.nickname} [{self.campaign.profile.country_code}]"

    # Unique identification data - required for all entries
    campaign = models.ForeignKey("Campaign", on_delete=models.SET_NULL, null=True)
    date = models.DateField(null=True)
    report_type = models.CharField(max_length=99, default="")  # SpReportType

    # Baseline data - obtained from SP report
    impressions = models.PositiveIntegerField(default=0, null=True)
    clicks = models.PositiveIntegerField(default=0, null=True)
    spend = models.DecimalField(max_digits=8, decimal_places=2, default=0, null=True)
    sales = models.DecimalField(max_digits=8, decimal_places=2, default=0, null=True)  # attributedSales30d
    orders = models.PositiveIntegerField(default=0, null=True)  # attributedUnitsOrdered30d
    kenp_royalties = models.PositiveIntegerField(
        default=0, null=True
    )  # attributedKindleEditionNormalizedPagesRoyalties14d

    # Obtained from campaign placement report
    placement = models.CharField(
        max_length=254, default=""
    )  # Could be: Top of Search on-Amazon    Detail Page on-Amazon    Other on-Amazon

    # Additional report data - obtained from other reports
    top_of_search_impression_share = models.DecimalField(max_digits=8, decimal_places=2, default=0, null=True)
    ad_id = models.PositiveBigIntegerField(null=True)
    ad_group_id = models.PositiveBigIntegerField(null=True)
    ad_group_name = models.CharField(max_length=254, default="")
    keyword_id = models.PositiveBigIntegerField(null=True)
    keyword_text = models.CharField(max_length=254, default="")
    query = models.CharField(max_length=254, default="")
    match_type = models.CharField(
        max_length=99, default=""
    )  # Type of matching for the keyword or phrase used in bid. Must be one of: BROAD, PHRASE, or EXACT
    asin = models.CharField(max_length=99, default="")
    target_id = models.PositiveBigIntegerField(null=True)
    target_expression = models.CharField(max_length=254, default="")
    target_text = models.CharField(max_length=254, default="")
    target_type = models.CharField(max_length=99, default="")
    units_sold_14d = models.PositiveIntegerField(default=0, null=True)
    attributed_conversions_30d = models.PositiveIntegerField(default=0, null=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=(
                    "ad_id",
                    "keyword_id",
                    "target_id",
                    "asin",
                    "query",
                    "placement",
                    "campaign",
                    "date",
                    "report_type",
                ),
                name="unique_recent_report_data",
            ),
        )


class Report(BaseModel):
    """
    Reports model used to track requested reports for Celery
    """

    def __str__(self):
        return f"{self.report_type} report on server: {self.report_server} on profile: {self.profile_id}"

    REPORT_STATUS_CHOICES = [
        (ReportStatus.PENDING.value, "Pending"),
        (ReportStatus.PROCESSING.value, "Processing"),
        (ReportStatus.COMPLETED.value, "Success"),
        (ReportStatus.FAILURE.value, "Amazon Failure"),
        (ReportStatus.INTERNAL_PROCESSED.value, "Internal Processed"),
        (ReportStatus.INTERNAL_FAILURE.value, "Internal Failure"),
        (ReportStatus.EMPTY.value, "Empty"),
    ]

    report_id = models.CharField(max_length=254, default="", unique=True, db_index=True)
    profile_id = models.PositiveBigIntegerField(null=True)
    report_type = models.CharField(max_length=99, default="")
    report_status = models.CharField(
        max_length=99, choices=REPORT_STATUS_CHOICES, default=ReportStatus.PENDING
    )
    report_location = models.CharField(max_length=4056, default="")
    report_for_date = models.DateField(null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    report_server = models.CharField(max_length=99, default="")
    report_size = models.PositiveBigIntegerField(null=True, default=0)
    failure_reason = models.CharField(max_length=4096, blank=True)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("report_type", "profile_id", "start_date", "end_date"),
                name="unique_report",
            ),
        )


class Keyword(BaseModel):
    """
    Keywords and keyword bid recommendations model
    """

    KEYWORD_TYPE_CHOICES = [
        ("Positive", "Positive"),
        ("Negative", "Negative"),
    ]

    keyword_id = models.PositiveBigIntegerField(null=True)
    keyword_type = models.CharField(max_length=99, choices=KEYWORD_TYPE_CHOICES, default="Positive")
    campaign = models.ForeignKey(
        "Campaign",
        verbose_name=("Campaign"),
        on_delete=models.CASCADE,
    )
    ad_group_id = models.PositiveBigIntegerField(null=True)  # This will be blank for Campaign Negatives
    state = models.CharField(max_length=99, choices=STATE_CHOICES, default=SpState.ENABLED.value)
    keyword_text = models.CharField(max_length=99, default="")
    match_type = models.CharField(max_length=99, choices=MATCH_TYPE_CHOICES, default=MatchType.BROAD.value)
    bid = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    serving_status = models.CharField(
        max_length=99,
        choices=TARGET_SERVING_STATUS_CHOICES,
        default="TARGETING_CLAUSE_STATUS_LIVE",
        null=True,
    )
    last_updated_date_on_amazon = models.PositiveBigIntegerField(default=0, null=True)  # in epoch time

    def __repr__(self):
        return f"<{self.__class__}: {self.__class__.__name__} object (Internal id: {self.id}, External id: {self.keyword_id}, Campaign: {self.campaign}, Adgroup id: {self.ad_group_id} )>"


class Target(BaseModel):
    """
    ASINs and Categories targeting model with bid recommendations
    """

    TARGET_TYPE_CHOICES = [
        ("Positive", "Positive"),
        ("Negative", "Negative"),
    ]

    target_id = models.PositiveBigIntegerField(null=True)
    keyword_type = models.CharField(max_length=99, choices=TARGET_TYPE_CHOICES, default="Positive")
    campaign = models.ForeignKey("Campaign", verbose_name=("Campaign"), on_delete=models.CASCADE)
    ad_group_id = models.PositiveBigIntegerField(null=True)
    state = models.CharField(max_length=99, choices=STATE_CHOICES, default=SpState.ENABLED.value)
    resolved_expression_text = models.CharField(max_length=99, default="", null=True)
    resolved_expression_type = models.CharField(max_length=99, default="")
    targeting_type = models.CharField(
        max_length=99,
        choices=TARGETING_TYPE_CHOICES,
        default=SpExpressionType.MANUAL.value,
    )
    bid = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    serving_status = models.CharField(
        max_length=99,
        choices=TARGET_SERVING_STATUS_CHOICES,
        default="TARGETING_CLAUSE_STATUS_LIVE",
        null=True,
    )
    last_updated_date_on_amazon = models.PositiveBigIntegerField(default=0, null=True)  # in epoch time


class Book(BaseModel):
    """
    Books information for eBooks, paperbacks and hardbacks
    """

    FORMAT_CHOICES = [
        ("Paperback", "Paperback"),
        ("Kindle", "Kindle"),
        ("Hardcover", "Hardcover"),
        ("Mass Market Paperback", "Mass Market Paperback"),
        ("Leather Bound", "Leather Bound"),
        ("Spiral-bound", "Spiral-bound"),
    ]

    profile = models.ForeignKey("Profile", verbose_name=("Profile"), on_delete=models.SET_NULL, null=True)
    pages = models.PositiveIntegerField(null=True, default=DEFAULT_BOOK_LENGTH)
    kbs = models.PositiveIntegerField(null=True, default=0)
    format = models.CharField(max_length=99, choices=FORMAT_CHOICES, default="Paperback", null=True)
    asin = models.CharField(max_length=99, default="")
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    be_acos = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    reviews = models.PositiveIntegerField(null=True, default=0)
    title = models.TextField(default="", null=True)
    author = models.TextField(default="", null=True, blank=True)
    target_bsr = models.PositiveIntegerField(null=True, default=0)
    current_bsr = models.PositiveIntegerField(null=True, default=0, blank=True)
    managed = models.BooleanField(default=False)
    in_catalog = models.BooleanField(default=False)
    pages_updated = models.BooleanField(default=False)
    eligible = models.BooleanField(default=True)
    launch = models.BooleanField(default=False)
    conservative = models.BooleanField(default=False)
    publication_date = models.DateField(
        null=True, blank=True, default=None
    )  # only needs to be filled in for book with launch = True
    # each book should have a set of camapaigns for each purpose
    campaign_discovery = models.ForeignKey(
        "Campaign",
        verbose_name=("Discovery Campaign"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    campaign_research_kw = models.ForeignKey(
        "Campaign",
        verbose_name=("Keyword Research Campaign"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    campaign_research_cat = models.ForeignKey(
        "Campaign",
        verbose_name=("Category Research Campaign"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    campaign_scale_kw = models.ForeignKey(
        "Campaign",
        verbose_name=("Keyword Scale Campaign"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    campaign_scale_asin = models.ForeignKey(
        "Campaign",
        verbose_name=("ASIN Scale Campaign"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    campaign_gp = models.ForeignKey(
        "Campaign",
        verbose_name=("GP Campaign"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    campaigns = models.ManyToManyField("Campaign", related_name="books")

    def __str__(self):
        title_length = self.title.find(":")
        full_phrase = self.title[:title_length]
        full_phrase = full_phrase.strip()
        return full_phrase
    
    def save(self, *args, **kwargs):
        if self.be_acos is None:
            if self.format == 'Kindle':
                self.be_acos = DEFAULT_BE_ACOS_KINDLE
            else:
                self.be_acos = DEFAULT_BE_ACOS
        if self.price is None:
            if self.format == 'Kindle':
                self.price = DEFAULT_EBOOK_PRICE
            else:
                self.price = DEFAULT_BOOK_PRICE
        super().save(*args, **kwargs)

    @classmethod
    def get_eligibility(cls, eligibility_status) -> bool:
        if eligibility_status == "ELIGIBLE":
            return True

        return False

    def is_published_for_days(self, days):
        current_date = datetime.now()
        difference = current_date - self.publication_date
        return difference >= timedelta(days=days)



# class DefaultKeyword(BaseModel):
#     """
#     Negative, never-negative & highly relevant positive keywords per book
#     to be added to each new campaign created including that book
#     plus used to keyword research
#     """

#     KEYWORD_TYPE_CHOICES = [
#         ("Negative", "Negative"),
#         ("NeverNegative", "Never Negative"),
#         ("Positive", "Positive"),
#     ]

#     book = models.ForeignKey("Book", verbose_name=("Book"), on_delete=models.SET_NULL, null=True)
#     type = models.CharField(max_length=99, choices=KEYWORD_TYPE_CHOICES, default="Negative")
#     keyword_text = models.CharField(max_length=99, default="")


class NewRelease(BaseModel):
    """
    Newly released book information for creation of new campaigns
    """

    asin = models.CharField(max_length=99, default="")
    image_url = models.URLField(max_length=200, null=True, blank=True)
    title = models.CharField(max_length=250, default="", null=True)
    bsr = models.PositiveIntegerField(null=True, default=0, blank=True)
    country_code = models.CharField(
        max_length=10, choices=CountryCodeChoice.choices, default=CountryCodeChoice.US
    )

    def __str__(self):
        return f"{self.asin} [{self.country_code}]"


class Relevance(BaseModel):
    """
    Connecting (intermediary) DB for Source books and Target new releases
    """

    book = models.ForeignKey("Book", verbose_name=("Book"), on_delete=models.SET_NULL, null=True)
    new_release = models.ForeignKey(
        "NewRelease", verbose_name=("New Release"), on_delete=models.SET_NULL, null=True
    )
    relevant = models.BooleanField(default=False)
    checked = models.BooleanField(default=False)
    targeting = models.BooleanField(default=False)


class Rank(BaseModel):
    """
    Rank of a book on a keyword covering Sponsored Brands, Sponsored Products and Organic Rank
    """

    book = models.ForeignKey("Book", verbose_name=("Book"), on_delete=models.SET_NULL, null=True)
    keyword = models.CharField(max_length=250, default="", null=True, blank=True)
    rank_sb = models.PositiveIntegerField(default=0)
    rank_sp = models.PositiveIntegerField(default=0)
    rank_org = models.PositiveIntegerField(default=0)


class DateBookPrice(models.Model):
    date = models.DateField()
    book = models.ForeignKey("Book", on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=DEFAULT_BOOK_PRICE)

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("date", "book"),
                name="unique_date_book_price",
            ),
        )
