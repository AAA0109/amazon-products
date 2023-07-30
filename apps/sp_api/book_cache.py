from functools import wraps

from apps.sp_api.models import BookCache


def cached_title(func):
    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        asin = kwargs.get("asin")
        try:
            book_cache: BookCache = BookCache.objects.get(asin=asin)
            if book_cache.outdated:
                title, bsr = func(cls, *args, **kwargs)
                book_cache.bsr = bsr
                book_cache.title = title
                book_cache.save()

        except BookCache.DoesNotExist:
            title, bsr = func(cls, *args, **kwargs)
            BookCache(asin=asin, title=title, bsr=bsr).save()
        else:
            title = book_cache.title
            bsr = book_cache.bsr

        return title, bsr
    return wrapper
