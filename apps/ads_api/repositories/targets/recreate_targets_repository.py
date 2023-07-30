from typing import Any

from apps.ads_api.entities.amazon_ads.sponsored_products.targets import (
    Expression,
    TargetEntity,
)
from apps.ads_api.models import Target


class RecreateTargetsRepository:
    @staticmethod
    def retrieve_targets_to_recraete(campaign: dict) -> list[dict[str, Any]]:
        targets = Target.objects.filter(
            campaign_id=campaign["id"],
            ad_group_id=campaign["ad_groups__ad_group_id"],
            target_id__isnull=True,
        )

        return [
            TargetEntity(
                campaign_id=campaign["campaign_id_amazon"],
                ad_group_id=campaign["ad_groups__ad_group_id"],
                bid=target.bid,
                state=target.state,
                expression=[
                    Expression(
                        type=target.resolved_expression_type,
                        value=target.resolved_expression_text,
                    )
                ],
                expression_type=target.targeting_type,
            ).dict(exclude_none=True, by_alias=True)
            for target in targets
        ]
