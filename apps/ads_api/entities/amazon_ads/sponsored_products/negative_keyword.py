from typing import Optional

from pydantic import BaseModel, Field

from apps.ads_api.constants import SpState, NegativeMatchType
from apps.ads_api.entities.amazon_ads.sponsored_products.extended_data import ExtendedData


class NegativeKeywordEntity(BaseModel):
    external_id: Optional[str] = Field(alias="keywordId")
    native_language_keyword: Optional[str] = Field(alias="nativeLanguageKeyword")
    native_language_locale: Optional[str] = Field(alias="nativeLanguageLocale")
    campaign_id: Optional[str] = Field(alias="campaignId")
    match_type: Optional[NegativeMatchType] = Field(alias="matchType")
    state: Optional[SpState]
    ad_group_id: str = Field(alias="adGroupId")
    keyword_text: str = Field(alias="keywordText")
    extended_data: Optional[ExtendedData] = Field(alias="extendedData")

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True
