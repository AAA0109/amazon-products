import mock
import pytest
from mock.mock import MagicMock, Mock

from apps.ads_api.exceptions.ads_api.base import (
    BaseAmazonAdsException,
    ObjectNotCreatedError,
)
from apps.ads_api.exceptions.internal.exceptions import InvalidAsin
from apps.ads_api.google_sheets import RETRY_SHEET_NAME
from apps.ads_api.models import Book
from apps.ads_api.tasks import create_campaign_from_google_sheet


@pytest.fixture
def book(profile):
    profile.country_code = "US"
    profile.save()
    book = Book(asin="B07H65KP63", profile=profile)
    book.save()
    return book


@pytest.fixture
def dublicates_error_sample_response():
    return [
        {
            "errorType": "someTestError",
            "errorValue": {
                "duplicateValueError": {
                    "cause": {
                        "location": "test_location",
                        "trigger": "test_trigger",
                    },
                    "message": "Test error!",
                    "reason": "some test reason",
                }
            },
        }
    ]


@pytest.fixture
def eligibility_error_sample_response():
    return [
        {
            "errorType": "adEligibilityError",
            "errorValue": {
                "adEligibilityError": {
                    "cause": {},
                    "message": "Product is ineligible for advertising",
                    "reason": "AD_INELIGIBLE",
                }
            },
        }
    ]


@pytest.mark.django_db
class TestCreateCampaignFromGoogleSheet:
    @mock.patch(
        "apps.ads_api.google_sheets.GoogleSheet._initialize_client",
        return_value=MagicMock(),
    )
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.get_new_campaign_info")
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.move_created_campaign_to_output")
    @mock.patch("apps.ads_api.services.books.eligibility_service.BookElgibilityService.refresh")
    @mock.patch(
        "apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter.BaseSponsoredProductsAdapter.create"
    )
    @mock.patch("apps.ads_api.tasks.PostCreateCampaignSync.sync")
    def test_base_amazon_exception_raises_on_bad_response(
        self,
        post_sync_mock: Mock,
        adapter_create_mock: Mock,
        eligibility_refresh_mock: Mock,
        move_created_campaign_to_output_mock: Mock,
        get_new_campaign_info_mock: Mock,
        initialize_client_mock: Mock,
        book,
        dublicates_error_sample_response,
    ):
        book.title = "test_title"
        book.eligible = True
        book.save()
        return_value = [
            "B07H65KP63",
            "US",
            "Product-Comp",
            "10.0",
            "Action",
            "Thriller",
            "Adventure",
        ]
        get_new_campaign_info_mock.side_effect = Mock(side_effect=[return_value, []])
        adapter_create_mock.side_effect = ObjectNotCreatedError(dublicates_error_sample_response)

        with pytest.raises(BaseAmazonAdsException):
            create_campaign_from_google_sheet()

        move_created_campaign_to_output_mock.assert_called_once()

    @mock.patch(
        "apps.ads_api.google_sheets.GoogleSheet._initialize_client",
        return_value=MagicMock(),
    )
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.get_new_campaign_info")
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.move_created_campaign_to_output")
    @mock.patch("apps.ads_api.services.books.eligibility_service.BookElgibilityService.refresh")
    @mock.patch(
        "apps.ads_api.adapters.amazon_ads.sponsored_products.base_sp_adapter.BaseSponsoredProductsAdapter._bulk_create_or_update"
    )
    @mock.patch("apps.ads_api.campaigns.base_campaign.BaseCampaign.create_campaign")
    @mock.patch("apps.ads_api.campaigns.base_campaign.BaseCampaign.create_ad_group_for_campaign")
    @mock.patch("apps.ads_api.tasks.PostCreateCampaignSync.sync")
    def test_campaign_written_to_retry_sheet_due_to_ineligible_product_error(
        self,
        post_sync_mock: Mock,
        adapter_create_mock_ad_group: Mock,
        adapter_create_mock_campaign: Mock,
        adapter_create_mock_product_ad: Mock,
        eligibility_refresh_mock: Mock,
        move_created_campaign_to_output_mock: Mock,
        get_new_campaign_info_mock: Mock,
        initialize_client_mock: Mock,
        book,
        eligibility_error_sample_response,
    ):
        book.title = "test_title"
        book.eligible = True
        book.save()
        return_value = [
            "B07H65KP63",
            "US",
            "Product-Comp",
            "10.0",
            "Action",
            "Thriller",
            "Adventure",
        ]
        adapter_create_mock_ad_group.return_value = Mock(campaign_id="1", external_id="1")
        get_new_campaign_info_mock.side_effect = Mock(side_effect=[return_value, []])
        adapter_create_mock_product_ad.return_value = [
            [],
            eligibility_error_sample_response,
        ]

        create_campaign_from_google_sheet()

        assert (
            move_created_campaign_to_output_mock.call_args.kwargs["campaign_info"][4][38:]
            == "Product[B07H65KP63] is ineligible for advertising"
        )
        assert move_created_campaign_to_output_mock.call_args.kwargs["write_sheet_name"] == RETRY_SHEET_NAME

    @mock.patch(
        "apps.ads_api.google_sheets.GoogleSheet._initialize_client",
        return_value=MagicMock(),
    )
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.get_new_campaign_info")
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.move_created_campaign_to_output")
    def test_invalid_asin_exception_raises_on_invalid_asin(
        self, move_created_campaign_to_output_mock, get_new_campaign_info_mock, initialize_client_mock
    ):
        return_value = [
            "B07H65KP6323213213123",
            "US",
            "Movie",
            "10.0",
            "Action",
            "Thriller",
            "Adventure",
        ]
        get_new_campaign_info_mock.side_effect = [return_value, []]

        create_campaign_from_google_sheet()
        assert move_created_campaign_to_output_mock.called is True

    @mock.patch(
        "apps.ads_api.google_sheets.GoogleSheet._initialize_client",
        return_value=MagicMock(),
    )
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.get_new_campaign_info")
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.move_created_campaign_to_output")
    def test_move_created_campaign_to_output_called_if_no_book_retrieved(
        self,
        move_created_campaign_to_output_mock: Mock,
        get_new_campaign_info_mock: Mock,
        initialize_client_mock: Mock,
    ):
        return_value = [
            "B07H65KP63",
            "US",
            "Movie",
            "10.0",
            "Action",
            "Thriller",
            "Adventure",
        ]

        get_new_campaign_info_mock.side_effect = Mock(side_effect=[return_value, []])

        create_campaign_from_google_sheet()

        move_created_campaign_to_output_mock.assert_called_once()

    @mock.patch(
        "apps.ads_api.google_sheets.GoogleSheet._initialize_client",
        return_value=MagicMock(),
    )
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.get_new_campaign_info")
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.move_created_campaign_to_output")
    @mock.patch("apps.ads_api.services.books.eligibility_service.BookElgibilityService.refresh")
    def test_move_created_campaign_to_output_called_if_book_has_no_titile(
        self,
        eligibility_refresh_mock: Mock,
        move_created_campaign_to_output_mock: Mock,
        get_new_campaign_info_mock: Mock,
        initialize_client_mock: Mock,
        book,
    ):
        return_value = [
            "B07H65KP63",
            "US",
            "Movie",
            "10.0",
            "Action",
            "Thriller",
            "Adventure",
        ]
        get_new_campaign_info_mock.side_effect = Mock(side_effect=[return_value, []])

        create_campaign_from_google_sheet()

        move_created_campaign_to_output_mock.assert_called_once()

    @mock.patch(
        "apps.ads_api.google_sheets.GoogleSheet._initialize_client",
        return_value=MagicMock(),
    )
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.get_new_campaign_info")
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.move_created_campaign_to_output")
    @mock.patch("apps.ads_api.services.books.eligibility_service.BookElgibilityService.refresh")
    def test_move_created_campaign_to_output_called_if_book_has_not_accessible_profile(
        self,
        eligibility_refresh_mock: Mock,
        move_created_campaign_to_output_mock: Mock,
        get_new_campaign_info_mock: Mock,
        initialize_client_mock: Mock,
        book,
    ):
        book.profile.accessible = False
        book.profile.save()
        return_value = [
            "B07H65KP63",
            "US",
            "Movie",
            "10.0",
            "Action",
            "Thriller",
            "Adventure",
        ]
        get_new_campaign_info_mock.side_effect = Mock(side_effect=[return_value, []])

        create_campaign_from_google_sheet()

        move_created_campaign_to_output_mock.assert_called_once()

    @mock.patch(
        "apps.ads_api.google_sheets.GoogleSheet._initialize_client",
        return_value=MagicMock(),
    )
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.get_new_campaign_info")
    @mock.patch("apps.ads_api.google_sheets.GoogleSheet.move_created_campaign_to_output")
    @mock.patch("apps.ads_api.services.books.eligibility_service.BookElgibilityService.refresh")
    def test_move_created_campaign_to_output_called_if_book_not_eligible(
        self,
        eligibility_refresh_mock: Mock,
        move_created_campaign_to_output_mock: Mock,
        get_new_campaign_info_mock: Mock,
        initialize_client_mock: Mock,
        book,
    ):
        book.title = "test_title"
        book.eligible = False
        return_value = [
            "B07H65KP63",
            "US",
            "Movie",
            "10.0",
            "Action",
            "Thriller",
            "Adventure",
        ]
        get_new_campaign_info_mock.side_effect = Mock(side_effect=[return_value, []])

        create_campaign_from_google_sheet()

        move_created_campaign_to_output_mock.assert_called_once()
