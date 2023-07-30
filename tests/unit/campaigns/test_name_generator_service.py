import pytest

from apps.ads_api.services.campaigns.name_generator_service import (
    CampaignNameGeneratorService,
)


@pytest.mark.django_db
class TestNameValidatorService:
    def test_number_in_name_increased_by_one(self, book, campaign):
        campaign.books.add(book)
        campaign.save()
        book.asin = "1801019959"
        book.save()

        name_generator = CampaignNameGeneratorService("Auto-Discovery-Complements", book, 0)
        new_name = name_generator.get_name()
        assert new_name == "T-SP-Auto-Discovery-Complements-2-1801019959-Paperback"
