from apps.ads_api.services.keywords.cleaner_service import KeywordsCleanerService


class TestKeywordsCleanerService:
    def test_clean_keywords(self):
        keywords = ["Hello", "world", "test", "test", "testing", "database", "project", "installation"]
        cleaner = KeywordsCleanerService(keywords=keywords)
        cleaned_keywords = cleaner.clean_keywords()
        expected_result = ["hello", "world", "test", "testing", "database", "project", "installation"]
        assert set(cleaned_keywords) == set(expected_result)

    def test_missing_characters_filled_with_0(self):
        keywords = ["23456789"]
        cleaner = KeywordsCleanerService(keywords=keywords)
        cleaned_keywords = cleaner.clean_keywords(is_asins=True)
        expected_result = ["0023456789"]
        assert cleaned_keywords == expected_result

    def test_clean_keywords_singularize(self):
        keywords = ["cars", "apples", "oranges", "databases", "projects", "installations"]
        cleaner = KeywordsCleanerService(keywords=keywords)
        cleaned_keywords = cleaner.clean_keywords(singularize=True)
        expected_result = ["apple", "orange", "database", "project", "installation"]
        assert set(cleaned_keywords) == set(expected_result)

    def test_clean_keywords_min_length(self):
        keywords = ["word", "as", "in", "a", "an"]
        cleaner = KeywordsCleanerService(keywords=keywords)
        cleaned_keywords = cleaner.clean_keywords()
        expected_result = ["word"]
        assert cleaned_keywords == expected_result

    def test_clean_keywords_common_words(self):
        keywords = ["the", "and", "a", "an", "for", "with", "you"]
        cleaner = KeywordsCleanerService(keywords=keywords)
        cleaned_keywords = cleaner.clean_keywords()
        expected_result = []
        assert cleaned_keywords == expected_result

    def test_clean_keywords_empty_input(self):
        keywords = []
        cleaner = KeywordsCleanerService(keywords=keywords)
        cleaned_keywords = cleaner.clean_keywords()
        expected_result = []
        assert cleaned_keywords == expected_result

    def test_clean_keywords_duplicate_input(self):
        keywords = ["hello", "world", "world"]
        cleaner = KeywordsCleanerService(keywords=keywords)
        cleaned_keywords = cleaner.clean_keywords()
        expected_result = ["hello", "world"]
        assert set(cleaned_keywords) == set(expected_result)
