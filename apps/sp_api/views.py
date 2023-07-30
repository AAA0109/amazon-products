from django.http import JsonResponse
from sp_api.api import Catalog
from sp_api.base import Marketplaces

from apps.ads_api.models import Book
from apps.sp_api import settings
from apps.sp_api.adapters.base_adapter import BaseSpApiAdapter
from apps.sp_api.adapters.book_catalog_adapter import BookCatalogAdapter
from apps.sp_api.catalog_api import CatalogAPI


def get_book_catalog(request):
    # book = Book.objects.first()
    # adapter = BookCatalogAdapter(profile=book.profile)
    # response = adapter.get_book_catalog(book.asin)
    res = Catalog(credentials=dict(
            refresh_token=settings.SP_API_REFRESH_TOKEN_NA,
            lwa_app_id=settings.SP_API_CLIENT_ID,
            lwa_client_secret=settings.SP_API_CLIENT_SECRET,
            aws_access_key=settings.AWS_ACCESS_KEY,
            aws_secret_key=settings.AWS_SECRET_KEY,
            role_arn=settings.ROLE_ARN,
    ), marketplace=Marketplaces.US).get_item('B08D6Z4H36', MarketplaceId='ATVPDKIKX0DER')
    return JsonResponse({"date": str("res")})

