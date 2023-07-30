from typing import Iterator, Optional

from pydantic import BaseModel, Field, root_validator, validator
from pydantic.types import date

from apps.ads_api.constants import ServerLocation, SpReportType
from apps.ads_api.models import ProductAd


class ReportEntity(BaseModel):
    report_id: str = Field(alias="reportId")
    report_size: Optional[int] = Field(alias="fileSize")
    report_type: Optional[SpReportType] = Field(alias="recordType")
    report_status: Optional[str] = Field(alias="status")
    report_location: Optional[str] = Field(alias="url")
    failure_reason: Optional[str] = Field(alias="failureReason", default="")
    start_date: Optional[date] = Field(alias="startDate", default="")
    end_date: Optional[date] = Field(alias="endDate", default="")
    profile_id: Optional[int]
    report_server: Optional[ServerLocation]

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True


class ReportListEntity(BaseModel):
    __root__: list[ReportEntity]

    def __iter__(self) -> Iterator[ReportEntity]:
        return iter(self.__root__)

    def __getitem__(self, item) -> ReportEntity:
        return self.__root__[item]

    def __len__(self):
        return len(self.__root__)


class BaseReportDataEntity(BaseModel):
    orders: int = Field(alias="unitsSoldClicks30d")
    sales: float = Field(alias="sales30d")
    kenp_royalties: int = Field(alias="kindleEditionNormalizedPagesRoyalties14d")
    campaign_id: int = Field(alias="campaignId")
    spend: float = Field(alias="cost")
    attributed_conversions_30d: int = Field(alias="purchases30d")
    impressions: int
    clicks: int

    date: Optional[date]
    report_type: Optional[str]
    # common fields to avoid AttributeError when saving ReportData
    ad_id: Optional[int]
    keyword_id: Optional[int]
    target_id: Optional[int]
    asin: Optional[str] = Field(alias="advertisedAsin", default="")
    query: str = Field(alias="searchTerm", default="")
    placement: str = Field(alias="placementClassification", default="")
    ad_group_name: str = Field(default="")
    ad_group_id: Optional[int]
    keyword_text: str = Field(alias="keyword", default="")
    match_type: str = Field(alias="matchType", default="")
    target_expression: str = Field(alias="keyword", default="")
    target_text: str = Field(alias="targeting", default="")
    target_type: str = Field(alias="keywordType", default="")

    @validator("orders")
    def replace_negative_orders(cls, v: int):
        return v if v >= 0 else 0

    @validator("kenp_royalties")
    def replace_negative_kenp_royalties(cls, v: int):
        return v if v >= 0 else 0

    @validator("attributed_conversions_30d")
    def replace_negative_attributed_conversions_30d(cls, v: int):
        return v if v >= 0 else 0

    @validator("impressions")
    def replace_negative_impressions(cls, v: int):
        return v if v >= 0 else 0

    @validator("clicks")
    def replace_negative_clicks(cls, v: int):
        return v if v >= 0 else 0

    class Config:
        allow_population_by_field_name = True


class CampaignsReportDataEntity(BaseReportDataEntity):
    top_of_search_impression_share: Optional[float] = Field(alias="topOfSearchImpressionShare")
    pass


class KeywordQueryReportDataEntity(BaseReportDataEntity):
    keyword_id: int = Field(alias="keywordId")
    ad_group_name: str = Field(alias="adGroupName")
    query: Optional[str] = Field(alias="searchTerm", default="")
    match_type: str = Field(alias="matchType")
    ad_group_id: int = Field(alias="adGroupId")
    keyword_text: str = Field(alias="keyword", default="")


class KeywordsReportDataEntity(BaseReportDataEntity):
    keyword_id: int = Field(alias="keywordId")
    ad_group_name: str = Field(alias="adGroupName")
    match_type: str = Field(alias="matchType")
    ad_group_id: int = Field(alias="adGroupId")
    keyword_text: Optional[str] = Field(alias="keyword", default="")

    @validator("match_type")
    def country_code_to_lower(cls, v: str):
        return v.lower()


class PlacementsReportDataEntity(BaseReportDataEntity):
    placement: str = Field(alias="placementClassification")


class ProductAdsReportData(BaseReportDataEntity):
    ad_id: int = Field(alias="adId")
    ad_group_name: str = Field(alias="adGroupName")
    asin: Optional[str] = Field(alias="advertisedAsin")
    ad_group_id: int = Field(alias="adGroupId")

    @root_validator
    def replace_none_with_blank(cls, values):
        if values.get("asin") is None:
            ad_group_name: str = values.get("ad_group_name")
            try:
                values["asin"] = ad_group_name.split("-")[-2]
            except IndexError:
                values["asin"] = ""

            if len(values["asin"]) != 10:
                values["asin"] = cls._resolve_asin_from_db(values["ad_id"])

        return values

    @classmethod
    def _resolve_asin_from_db(cls, ad_id) -> str:
        product_ads = ProductAd.objects.filter(product_ad_id=ad_id).first()
        if product_ads:
            asin = product_ads.asin
        else:
            asin = ""
        return asin


class TargetQueryReportDataEntity(BaseReportDataEntity):
    target_id: int = Field(alias="keywordId")
    ad_group_name: str = Field(alias="adGroupName")
    query: str = Field(alias="searchTerm")
    target_expression: str = Field(alias="keyword")
    ad_group_id: int = Field(alias="adGroupId")
    target_text: str = Field(alias="targeting")
    target_type: str = Field(alias="keywordType")


class TargetsReportData(BaseReportDataEntity):
    target_id: int = Field(alias="keywordId")
    ad_group_name: str = Field(alias="adGroupName")
    target_expression: str = Field(alias="keyword")
    ad_group_id: int = Field(alias="adGroupId")
    target_text: str = Field(alias="targeting")
    target_type: str = Field(alias="keywordType")
