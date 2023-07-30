import pytest

from apps.ads_api.constants import AdStatus, SpState
from apps.ads_api.models import CampaignPurpose, ProductAd
from apps.ads_api.repositories.book.book_repository import BookRepository
from apps.ads_api.repositories.campaign_repository import CampaignRepository
from apps.ads_api.repositories.product_ad_repository import ProductAdRepository


@pytest.fixture
def asins():
    return [f"asin{indx}" for indx in range(5)]


@pytest.fixture
def books(asins, profile):
    return [
        BookRepository.create(asin=asin, profile=profile) for asin in asins
    ]


@pytest.fixture
def product_ads(asins, campaign, ad_group):
    product_ads = [
        ProductAd.objects.create(
            asin=asin,
            state=AdStatus.ENABLED,
            product_ad_id=indx,
            campaign=campaign,
            ad_group=ad_group
        )
        for indx, asin in enumerate(asins)
    ]
    for product_ad in product_ads[:2]:
        product_ad.state = AdStatus.PAUSED
        product_ad.save()
    return product_ads


@pytest.fixture
def campaign_with_product_ads(books, campaign, profile, product_ads):
    CampaignRepository.set_product_ads_for_campaign(campaign, product_ads)
    campaign.profile = profile
    campaign.save()
    return campaign


@pytest.mark.django_db
def test_exists_by_returns_true_if_exists(campaign, book):
    campaign.campaign_purpose = CampaignPurpose.Discovery
    campaign.state = SpState.ENABLED.value
    campaign.campaign_name__contains = "Complements"
    campaign.save()

    is_exists = CampaignRepository.exists_by(
        **{
            "campaign_purpose": CampaignPurpose.Discovery,
            "state": SpState.ENABLED.value,
            "campaign_name__contains": "Complements",
        }
    )
    assert is_exists is True


@pytest.mark.django_db
def test_book_was_added_to_campaign(campaign, book):
    CampaignRepository.add_books_for_campaign(campaign, (book,))
    assert campaign.books.get(id=book.id) == book


@pytest.mark.django_db
def test_books_were_updated_by_contained_product_ads(
    profile, campaign_with_product_ads, asins
):
    CampaignRepository.update_books_by_contained_product_ads_for_profiles([profile.id])
    product_ads = ProductAdRepository.retrieve_by_kwargs(
        state__iexact=AdStatus.ENABLED
    )
    asins_after_update = ProductAdRepository.retrieve_asins_from_product_ads(
        product_ads
    )

    _assert_all_asins_in_campaign(campaign_with_product_ads, asins_after_update)


def _assert_all_asins_in_campaign(campaign, expected_asins):
    assert set(campaign.books.values_list("asin", flat=True)) == set(expected_asins)
