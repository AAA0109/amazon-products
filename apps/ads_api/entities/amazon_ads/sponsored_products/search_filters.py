from typing import Optional

from pydantic import BaseModel, Field

from apps.ads_api.constants import (
    QueryTermMatchType,
    SpState, MatchType, NegativeMatchType, SpExpressionType,
)


class IdFilter(BaseModel):
    include: Optional[list[str]]


class StateFilter(BaseModel):
    include: Optional[list[SpState]] = Field(max_items=10)

    class Config:
        use_enum_values = True


class TextFilter(BaseModel):
    query_term_match_type: Optional[QueryTermMatchType] = Field(alias="queryTermMatchType")
    include: list[str] = Field(max_items=100)

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class ExpressionTypeFilter(BaseModel):
    include: list[SpExpressionType] = Field(max_items=2)


class BaseFilter(BaseModel):
    """
    A base Pydantic model representing common fields for filters used in API requests.

    :argument:
    - state_filter: Optional[StateFilter]. Filter by state.
    - max_results: Optional[int]. Maximum number of results to be returned.
    - next_token: Optional[str]. Token used for pagination.
    - include_extended_data_fields: Optional[bool]. Whether to include extended data fields in the response.
    """
    state_filter: Optional[StateFilter] = Field(alias="stateFilter")
    max_results: Optional[int] = Field(alias="maxResults")
    next_token: Optional[str] = Field(alias="nextToken")
    include_extended_data_fields: Optional[bool] = Field(
        default=True, alias="includeExtendedDataFields"
    )

    class Config:
        use_enum_values = True
        allow_population_by_field_name = True


class AdGroupSearchFilter(BaseFilter):
    campaign_id_filter: Optional[IdFilter] = Field(alias="campaignIdFilter")
    ad_group_id_filter: Optional[IdFilter] = Field(alias="adGroupIdFilter")
    name_filter: Optional[TextFilter] = Field(alias="nameFilter")
    campaign_targeting_type_filter: Optional[str] = Field(alias="campaignTargetingTypeFilter")


class CampaignSearchFilter(BaseFilter):
    campaign_id_filter: Optional[IdFilter] = Field(alias="campaignIdFilter")
    portfolio_id_filter: Optional[IdFilter] = Field(alias="portfolioIdFilter")
    name_filter: Optional[TextFilter] = Field(alias="nameFilter")


class ProductAdSearchFilter(BaseFilter):
    campaign_id_filter: Optional[IdFilter] = Field(alias="campaignIdFilter")
    ad_id_filter: Optional[IdFilter] = Field(alias="adIdFilter")
    ad_group_id_filter: Optional[IdFilter] = Field(alias="adGroupIdFilter")


class KeywordSearchFilter(BaseFilter):
    campaign_id_filter: Optional[IdFilter] = Field(alias="campaignIdFilter")
    ad_group_id_filter: Optional[IdFilter] = Field(alias="adGroupIdFilter")
    locale: Optional[str]
    text_filter: Optional[TextFilter] = Field(alias="keywordTextFilter")
    keyword_id_filter: Optional[IdFilter] = Field(alias="keywordIdFilter")
    match_type_filter: Optional[MatchType] = Field(alias="matchTypeFilter")


class TargetSearchFilter(BaseFilter):
    campaign_id_filter: Optional[IdFilter] = Field(alias="campaignIdFilter")
    target_id_filter: Optional[IdFilter] = Field(alias="targetIdFilter")
    asin_filter: Optional[TextFilter] = Field(alias="asinFilter")
    ad_group_id_filter: Optional[IdFilter] = Field(alias="adGroupIdFilter")
    expression_type_filter: Optional[ExpressionTypeFilter] = Field(alias="expressionTypeFilter")


class NegativeKeywordSearchFilter(BaseFilter):
    text_filter: Optional[TextFilter] = Field(alias="negativeKeywordTextFilter")
    campaign_id_filter: Optional[IdFilter] = Field(alias="campaignIdFilter")
    ad_group_id_filter: Optional[IdFilter] = Field(alias="adGroupIdFilter")
    locale: Optional[str]
    negative_keyword_id_filter: Optional[IdFilter] = Field(
        alias="negativeKeywordIdFilter"
    )
    match_type_filter: Optional[NegativeMatchType] = Field(alias="matchTypeFilter")


class CampaignNegativeKeywordSearchFilter(BaseFilter):
    text_filter: Optional[TextFilter] = Field(
        alias="campaignNegativeKeywordTextFilter"
    )
    campaign_id_filter: Optional[IdFilter] = Field(alias="campaignIdFilter")
    ad_group_id_filter: Optional[IdFilter] = Field(alias="adGroupIdFilter")
    locale: Optional[str]
    campaign_negative_keyword_id_filter: Optional[IdFilter] = Field(
        alias="campaignNegativeKeywordIdFilter"
    )
    match_type_filter: Optional[NegativeMatchType] = Field(alias="matchTypeFilter")


class NegativeTargetSearchFilter(BaseFilter):
    negative_target_id_filter: Optional[IdFilter] = Field(
        alias="negativeTargetIdFilter"
    )
    campaign_id_filter: Optional[IdFilter] = Field(alias="campaignIdFilter")
    asin_filter: Optional[TextFilter] = Field(alias="asinFilter")
    ad_group_id_filter: Optional[IdFilter] = Field(alias="adGroupIdFilter")


class CampaignNegativeTargetSearchFilter(BaseFilter):
    campaign_id_filter: Optional[IdFilter] = Field(alias="campaignIdFilter")
    campaign_negative_target_id_filter: Optional[IdFilter] = Field(
        alias="campaignNegativeTargetIdFilter"
    )
    asin_filter: Optional[TextFilter] = Field(alias="asinFilter")
