from django.db.models import QuerySet

from apps.ads_api.models import Target


class TargetsRepository:
    @staticmethod
    def create_by_kwargs(**kwargs) -> Target:
        return Target.objects.create(**kwargs)

    @staticmethod
    def retrieve_all() -> QuerySet[Target]:
        return Target.objects.all()
