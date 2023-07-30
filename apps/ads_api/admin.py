import datetime
import logging
from collections import defaultdict
from decimal import Decimal

from django.contrib import admin

from apps.ads_api.adapters.amazon_ads.sponsored_products.campaigns_adapter import (
    CampaignAdapter,
)
from apps.ads_api.constants import PRODUCT_AD_VALID_STATUSES
from apps.ads_api.entities.amazon_ads.sponsored_products.search_filters import (
    CampaignSearchFilter,
    IdFilter,
)

from .models import (
    AdGroup,
    Book,
    Campaign,
    Keyword,
    ProductAd,
    Profile,
    RecentReportData,
    Relevance,
    Report,
    ReportData,
    Target,
)
from .tasks import get_profile_book_catalog, turn_on_profit_mode

_logger = logging.getLogger(__name__)

# Register your models here.


@admin.action(description="Toggle managed")
def toggle_managed(modeladmin, request, queryset):
    for entry in queryset:
        if entry.managed == True:
            entry.managed = False
        else:
            entry.managed = True
        entry.save()


@admin.action(description="Get profile book catalog")
def get_profile_book_catalog_admin(modeladmin, request, queryset):
    get_profile_book_catalog.delay([obj.id for obj in queryset.all()])


@admin.action(description="Turn on profit mode")
def turn_on_profit_mode_admin(modeladmin, request, queryset: Profile):
    turn_on_profit_mode(queryset)


@admin.action(description="New client sync")
def new_client_sync_admin(modeladmin, request, queryset: Profile):
    raise NotImplemented


@admin.register(RecentReportData)
class RecentReportDataAdmin(admin.ModelAdmin):
    pass


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    class ReviewsFilter(admin.SimpleListFilter):
        title = "number of reviews"
        parameter_name = "review_number"

        def lookups(self, request, model_admin):
            return (
                (">=100", ">=100"),
                (">=15", ">=15"),
                ("5-14", "5-14"),
                ("1-4", "1-4"),
                ("0", "0"),
            )

        def queryset(self, request, queryset):
            value = self.value()
            if value == ">=100":
                return queryset.filter(reviews__gte=100)
            elif value == ">=15":
                return queryset.filter(reviews__gte=15)
            elif value == "5-14":
                return queryset.filter(reviews__lte=14, reviews__gte=5)
            elif value == "1-4":
                return queryset.filter(reviews__lte=4, reviews__gte=1)
            elif value == "0":
                return queryset.filter(reviews=0)

    class ValidTitle(admin.SimpleListFilter):
        title = "title is valid"
        parameter_name = "valid_title"

        def lookups(self, request, model_admin):
            return (
                ("Yes", "Yes"),
                ("No", "No"),
            )

        def queryset(self, request, queryset):
            value = self.value()
            if value == "Yes":
                return queryset.exclude(title="")
            elif value == "No":
                return queryset.filter(title="")

    @admin.display(description="Running Product Ads")
    def get_running_product_ad_count(self, obj):
        book_product_ads_db_count = ProductAd.objects.filter(
            serving_status__in=PRODUCT_AD_VALID_STATUSES,
            campaign__profile=obj.profile,
            asin=obj.asin,
        ).count()
        return book_product_ads_db_count

    list_display = [
        "title",
        "author",
        "get_country_code",
        "format",
        "asin",
        "be_acos",
        "reviews",
        "get_running_product_ad_count",
        "managed",
        "get_nickname",
        "created_at",
        "eligible",
        "launch",
        "conservative",
        "publication_date",
    ]
    list_filter = [
        "profile__nickname",
        "format",
        "managed",
        "profile__country_code",
        "profile__managed",
        "eligible",
        ReviewsFilter,
        ValidTitle,
    ]
    autocomplete_fields = [
        "campaigns",
        "campaign_discovery",
        "campaign_research_kw",
        "campaign_research_cat",
        "campaign_scale_kw",
        "campaign_scale_asin",
        "campaign_gp",
    ]
    list_editable = ["managed", "launch", "conservative", "publication_date"]
    actions = [toggle_managed]
    search_fields = ["title", "asin", "author"]
    list_select_related = ["profile"]

    @admin.display(description="Book Entries")
    def get_dupe_books(self, obj):
        asin = obj.asin
        book_count = Book.objects.filter(
            profile=obj.profile,
            asin=asin,
        ).count()
        return book_count

    @admin.display(description="Market", ordering="profile__country_code")
    def get_country_code(self, obj):
        return obj.profile.country_code

    @admin.display(description="Profile")
    def get_nickname(self, obj):
        return obj.profile.nickname


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        "entity_id",
        "nickname",
        "marketplace_string_id",
        "managed",
        "accessible",
        "research_percentage",
        "profit_mode",
        "valid_payment_method",
        "profile_server",
        "monthly_budget",
        "surplus_budget",
    ]
    list_filter = [
        "nickname",
        "marketplace_string_id",
        "accessible",
        "profit_mode",
        "managed",
    ]
    list_editable = [
        "nickname",
        "managed",
        "profit_mode",
        "research_percentage",
        "monthly_budget",
    ]
    actions = [toggle_managed]
    search_fields = ["profile_id", "entity_id", "nickname"]
    actions = [
        toggle_managed,
        get_profile_book_catalog_admin,
        new_client_sync_admin,
        turn_on_profit_mode_admin,
    ]
    readonly_fields = ["surplus_budget"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        "report_type",
        "report_status",
        "report_for_date",
        "report_server",
        "get_profiles",
        "report_size",
    ]
    list_filter = ["report_status", "report_type"]
    search_fields = ["profile_id", "report_id"]
    date_hierarchy = "report_for_date"  # DateField

    @admin.display(description="Profile")
    def get_profiles(self, obj):
        profiles = Profile.objects.all()
        bool(profiles)
        profile_id = obj.profile_id
        first_profile = profiles.filter(profile_id=profile_id).first()
        nick = "N/A" if first_profile == None else first_profile.nickname
        return nick


@admin.register(ReportData)
class ReportDataAdmin(admin.ModelAdmin):
    list_display = [
        "campaign",
        "get_country_code",
        "date",
        "report_type",
        "impressions",
        "clicks",
        "spend",
        "sales",
        "kenp_royalties",
        "keyword_text",
        "query",
        "target_text",
    ]
    list_filter = [
        "campaign__profile__nickname",
        "campaign__profile__country_code",
        "report_type",
    ]
    date_hierarchy = "date"  # DateField
    search_fields = ["keyword_text", "target_text", "query", "campaign__campaign_name"]

    @admin.display(description="Market")
    def get_country_code(self, obj):
        return obj.campaign.profile.country_code


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     qs = qs.annotate(
    #         _keyword_count=Count("keyword", serving_status="TARGETING_CLAUSE_STATUS_LIVE", keyword_type="Positive")
    #         + Count("target", serving_status="TARGETING_CLAUSE_STATUS_LIVE", keyword_type="Positive")
    #     )
    #     return qs

    # @admin.display(description="Size")
    # def kwd_count(self, obj):
    #     return obj._keyword_count

    # kwd_count.admin_order_field = "_keyword_count"

    # class SizeFilter(admin.SimpleListFilter):
    #     title = "campaign_size"
    #     parameter_name = "campaign_size"

    #     def lookups(self, request, model_admin):
    #         return (
    #             ("Big", "Big"),
    #             ("Small", "Small"),
    #         )

    #     def queryset(self, request, queryset):
    #         value = self.value()
    #         if value == "Big":
    #             return queryset.filter(_keyword_count__gt=100)
    #         elif value == "Small":
    #             return queryset.exclude(_keyword_count__gt=100)
    #         return queryset

    @admin.action(description="Archive campaign from amazon")
    def archive(modeladmin, request, queryset):
        sorted_campaign_list = sorted(queryset, key=lambda k: k.profile.id)
        sorted_campaign_dict = defaultdict(list)
        for campaign in sorted_campaign_list:
            profile = campaign.profile
            campaign_id = campaign.campaign_id_amazon
            sorted_campaign_dict[profile].append(campaign_id)

        for profile, campaigns_id in sorted_campaign_dict.items():
            adapter = CampaignAdapter(profile)
            success, errors = adapter.delete(CampaignSearchFilter(IdFilter(include=campaigns_id)))
            _logger.info("Campaigns deleted %s", success)
            if errors:
                _logger.warning("Campaigns deleting errors %s", errors)

    @admin.action(description="Reset target ACOS")
    def reset_target_acos(modeladmin, request, queryset):
        for entry in queryset:
            entry.target_acos = Decimal(0.40)
            entry.save()

    list_display = [
        "campaign_name",
        "get_country_code",
        "serving_status",
        "state",
        "managed",
        "target_acos",
        "asins",
        "campaign_purpose",
        "sponsoring_type",
        # "kwd_count",
        "get_campaign_profile",
    ]
    list_filter = [
        "profile__nickname",
        "profile__country_code",
        "managed",
        "sponsoring_type",
        "state",
        "serving_status",
        "campaign_purpose",
        "profile__managed",
        # SizeFilter,
    ]
    search_fields = ["campaign_name", "asins"]
    list_select_related = ["profile"]
    actions = [toggle_managed, reset_target_acos, archive]  # type: ignore
    # empty_value_display = "not assigned"

    @admin.display(description="Market", ordering="profile__country_code")
    def get_country_code(self, obj):
        return obj.profile.country_code

    @admin.display(description="Profile")
    def get_campaign_profile(self, obj):
        return obj.profile.nickname


@admin.register(AdGroup)
class AdGroupAdmin(admin.ModelAdmin):
    list_display = [
        "ad_group_name",
        "get_campaign_name",
        "serving_status",
        "state",
        "manual_type",
        "default_bid",
    ]
    list_filter = [
        "campaign__profile__nickname",
        "campaign__profile__country_code",
        "state",
        "serving_status",
    ]
    search_fields = ["ad_group_name", "ad_group_id"]

    @admin.display(description="Campaign")
    def get_campaign_name(self, obj):
        return obj.campaign.campaign_name

    @admin.display(description="Country")
    def get_country(self, obj):
        return obj.campaign.profile.country_code


@admin.register(ProductAd)
class ProductAdAdmin(admin.ModelAdmin):
    list_display = [
        "asin",
        "serving_status",
        "state",
        "campaign",
    ]
    list_filter = [
        "campaign__profile__nickname",
        "campaign__profile__country_code",
        "state",
        "serving_status",
    ]
    search_fields = ["campaign__campaign_name", "asin"]


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = [
        "keyword_text",
        "campaign",
        "match_type",
        "serving_status",
        "convert_epoch_datetime",
    ]
    list_filter = [
        "campaign__profile__nickname",
        "campaign__profile__country_code",
        "state",
        "serving_status",
        "match_type",
    ]
    search_fields = ["campaign__campaign_name", "keyword_text", "campaign__asins"]

    @admin.display(description="Last change datetime")
    def convert_epoch_datetime(self, obj):
        # given epoch time
        epoch_time = obj.last_updated_date_on_amazon
        # using the datetime.fromtimestamp() function
        date_time = datetime.datetime.fromtimestamp(epoch_time / 1000)
        return date_time


@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = [
        "resolved_expression_text",
        "campaign",
        "serving_status",
        "keyword_type",
        "convert_epoch_datetime",
    ]
    list_filter = [
        "campaign__profile__nickname",
        "campaign__profile__country_code",
        "state",
        "serving_status",
        "keyword_type",
    ]
    search_fields = ["campaign__campaign_name", "resolved_expression_text"]

    @admin.display(description="Last change datetime")
    def convert_epoch_datetime(self, obj):
        # given epoch time
        epoch_time = obj.last_updated_date_on_amazon
        # using the datetime.fromtimestamp() function
        date_time = datetime.datetime.fromtimestamp(epoch_time / 1000)
        return date_time


@admin.register(Relevance)
class RelAdmin(admin.ModelAdmin):
    @admin.action(description="Checked")
    def checked(modeladmin, request, queryset):
        for entry in queryset:
            entry.checked = True
            entry.save()

    @admin.display(description="New release title")
    def get_new_release_title(self, obj):
        return obj.new_release.title

    list_display = [
        "book",
        "get_new_release_title",
        "new_release",
        "relevant",
        "checked",
        "targeting",
    ]
    list_filter = [
        "book__profile__country_code",
        "relevant",
        "checked",
        "targeting",
        "book__profile__nickname",
    ]
    actions = [checked]  # type: ignore
    search_fields = ["asin"]
    list_editable = ["relevant", "checked", "targeting"]
