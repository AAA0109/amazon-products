import logging
from typing import Any

from django.db.models import QuerySet

from apps.ads_api.entities.amazon_ads.sponsored_products.keywords import KeywordEntity
from apps.ads_api.models import AdGroup, Campaign, Keyword

_logger = logging.getLogger(__name__)


class KeywordsRepository:
    @staticmethod
    def create_by_kwargs(**kwargs) -> Keyword:
        return Keyword.objects.create(**kwargs)

    @staticmethod
    def retrieve_all() -> QuerySet[Keyword]:
        return Keyword.objects.all()

    @staticmethod
    def retrieve_keywords_to_recreate(campaign: dict) -> list[dict[str, Any]]:
        _logger.debug(f"Retrieving keywords for {campaign}")

        keywords = Keyword.objects.filter(
            campaign_id=campaign["id"],
            ad_group_id=campaign["ad_groups__ad_group_id"],
            keyword_id__isnull=True,
        )
        _logger.debug(f"Retrieved keywords {keywords}")

        return [
            KeywordEntity(
                campaign_id=campaign["campaign_id_amazon"],
                ad_group_id=campaign["ad_groups__ad_group_id"],
                keyword_text=keyword.keyword_text,
                bid=keyword.bid,
                state=keyword.state,
                match_type=keyword.match_type,
            ).dict(exclude_none=True, by_alias=True)
            for keyword in keywords
        ]

    @staticmethod
    def save_keywords_from_amazon(
        actual_created_keywords: list[KeywordEntity],
        expected_created_keywords: list[dict],
    ):
        keyword_text2keyword_entity_map = {k.keyword_text: k for k in actual_created_keywords}
        _logger.info("Keyword text to keyword to entity map: %s", keyword_text2keyword_entity_map)
        created_campaigns = {k.campaign_id for k in actual_created_keywords}
        created_ad_groups = {k.ad_group_id for k in actual_created_keywords}
        _logger.info("Created campaigns: %s", created_campaigns)
        _logger.info("Created ad_groups: %s", created_ad_groups)

        campaign_external_id2internal_id_map = {
            str(c["campaign_id_amazon"]): c["id"]
            for c in Campaign.objects.filter(campaign_id_amazon__in=created_campaigns).values(
                "campaign_id_amazon", "id"
            )
        }
        ad_group_external_id2id_map = {
            str(c["ad_group_id"]): c["id"]
            for c in AdGroup.objects.filter(ad_group_id__in=created_ad_groups).values("ad_group_id", "id")
        }

        text_keywords = [k["keywordText"] for k in expected_created_keywords]
        _logger.info("Text keywords: %s", text_keywords)
        keywords_to_create = []
        for text_keyword in text_keywords:
            keyword_to_create = Keyword(
                keyword_text=text_keyword,
                match_type=keyword_text2keyword_entity_map[text_keyword].match_type,
                state=keyword_text2keyword_entity_map[text_keyword].state,
                bid=keyword_text2keyword_entity_map[text_keyword].bid,
                keyword_id=keyword_text2keyword_entity_map[text_keyword].external_id,
                campaign_id=campaign_external_id2internal_id_map[
                    keyword_text2keyword_entity_map[text_keyword].campaign_id
                ],
                ad_group_id=ad_group_external_id2id_map[
                    keyword_text2keyword_entity_map[text_keyword].ad_group_id
                ],
            )
            if text_keyword in keyword_text2keyword_entity_map.keys():
                keyword_to_create.keyword_id = keyword_text2keyword_entity_map[text_keyword].external_id
            keywords_to_create.append(keyword_to_create)

        _logger.info("Total keywords to save: %s", keywords_to_create)
        Keyword.objects.bulk_create(keywords_to_create)
