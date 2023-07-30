from datetime import datetime, timedelta

import pytest
from django.test import override_settings

from apps.ads_api.models import Book
from apps.ads_api.tasks import update_books_launch_status


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_61_days_old_lauch_books_updated_with_launch_status_False(book: Book):
    book.launch = True
    book.publication_date = datetime.today() - timedelta(days=61)
    book.save()

    update_books_launch_status.delay()

    updated_book = Book.objects.get(id=book.id)
    assert updated_book.launch is False


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_20_days_old_lauch_books_not_updated(book: Book):
    book.launch = True
    book.publication_date = datetime.today() - timedelta(days=20)
    book.save()

    update_books_launch_status.delay()

    updated_book = Book.objects.get(id=book.id)
    assert updated_book.launch is True
