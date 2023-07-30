import logging

from django.db import models, ProgrammingError

_logger = logging.getLogger(__name__)

class BaseModel(models.Model):
    """
    Base model that includes default created / updated timestamps.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def delete_dublicates_by_fields(model, *fields):
    uniqs = model.objects.order_by(*fields).distinct(*fields)
    dubs = model.objects.exclude(id__in=uniqs)
    _logger.info("%s dublicates found.", dubs.count())
    try:
        model.objects.filter(id__in=dubs).delete()
    except ProgrammingError:
        for dub in dubs:
            dub.delete()


    uniqs = model.objects.order_by(*fields).distinct(*fields)
    dubs = model.objects.exclude(id__in=uniqs)
    _logger.info("%s dublicates found after cleaning.", dubs.count())


