from typing import Iterable

from apps.ads_api.adapters.amazon_ads.sponsored_products.negative_keywords_adapter import (
    NegativeKeywordsAdapter,
)
from apps.ads_api.constants import NegativeMatchType, SpState
from apps.ads_api.entities.amazon_ads.sponsored_products.campaign import CampaignEntity
from apps.ads_api.entities.amazon_ads.sponsored_products.negative_keyword import (
    NegativeKeywordEntity,
)
from apps.ads_api.models import Book


class FormatNegativesCreationService:
    def __init__(self, book: Book):
        self.book = book

    def add_format_negatives_to_campagins(self, campaigns: Iterable[CampaignEntity]):
        adapter = NegativeKeywordsAdapter(self.book.profile)

        formats = ["paperback", "kindle", "hardcover", "audiobook"]
        book_format = self.book.format.lower()
        formats.remove(book_format)
        if book_format != "kindle":
            formats.append("ebook")

        negatives_to_create: list[dict] = []
        for campaign in campaigns:
            for format_ in formats:
                negatives_to_create.append(
                    NegativeKeywordEntity(
                        campaign_id=campaign.external_id,
                        ad_group_id=campaign.external_id,
                        keyword_text=format_,
                        state=SpState.ENABLED,
                        match_type=NegativeMatchType.PHRASE,
                    ).dict(exclude_none=True, by_alias=True)
                )
        return adapter.batch_create(negatives_to_create)
