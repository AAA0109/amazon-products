from datetime import datetime, timezone

from django.db import models

from apps.utils.models import BaseModel


class BookCache(BaseModel):
    asin = models.CharField(max_length=10, null=False, blank=False, unique=True, db_index=True)
    title = models.CharField(max_length=2048, null=False, blank=False)
    bsr = models.IntegerField(null=False, blank=False)

    def __repr__(self):
        return f"BookCache(asin={self.asin}, bsr={self.bsr})"

    def __str__(self):
        return f"BookCache: asin={self.asin}, bsr={self.bsr}, title={self.title}"

    @property
    def outdated(self) -> bool:
        """Returns a boolean flag indicating whether the BookCache object is outdated.
        """
        now = datetime.now(timezone.utc)
        delta = now - self.updated_at
        return delta.days > 3
