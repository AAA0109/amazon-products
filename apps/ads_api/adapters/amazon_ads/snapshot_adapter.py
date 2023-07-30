from apps.ads_api.adapters.amazon_ads.base_amazon_ads_adapter import (
    BaseAmazonAdsAdapter,
)
from apps.ads_api.models import Profile


class SnapShotAdapter(BaseAmazonAdsAdapter):
    def __init__(self, profile: Profile):
        super().__init__(profile.profile_server)
        self.profile = profile

    def request(self, record_type: str):
        return self.send_request(
            url=f"/v2/sp/{record_type}/snapshot",
            method="POST",
            extra_headers={
                "Amazon-Advertising-API-Scope": str(self.profile.profile_id),
                "Content-Type": "application/json",
                "recordType": record_type,
            },
        )

    def get(self, snapshot_id: str):
        return self.send_request(
            url=f"/v2/sp/snapshots/{snapshot_id}",
            method="GET",
            extra_headers={
                "Amazon-Advertising-API-Scope": str(self.profile.profile_id),
                "Content-Type": "application/json",
            },
        )

    def donload(self, snapshot_id: str):
        def is_generated() -> bool:
            return self.get(snapshot_id).json()["status"] == "SUCCESS"

        if is_generated():
            return self.send_request(
                url=f"/v2/sp/snapshots/{snapshot_id}/download",
                method="GET",
                extra_headers={
                    "Amazon-Advertising-API-Scope": str(self.profile.profile_id),
                    "Content-Type": "application/json",
                },
            )
