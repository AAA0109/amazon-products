import string
import json
import os
from typing import List, Optional

import inflect

from apps.ads_api.constants import TOP_50_COMMON_KEYWORDS


class KeywordsCleanerService:
    def __init__(self, keywords: List[str]):
        """
        Args:
            keywords (List[str]): A list of keyword strings to be cleaned up.
        """
        self._keywords = keywords

    def clean_keywords(
        self, is_asins: Optional[bool] = False, singularize: Optional[bool] = True, marketplace: Optional[str] = "US"
    ) -> List[str]:
        """Cleans up a list of keywords by making them all lowercase, removing punctuation,
        removing any duplicates, and filtering the list to only include keywords that are 10
        characters in length if `is_asins` is True. Optionally simplifies the keywords to
        singular form (if applicable) if `singularize` is True.

        Args:
            is_asins (Optional[bool]): If True, the resulting list will only include
                keywords that are 10 characters in length.
            singularize (Optional[bool]): If True, the resulting list will include simplified
                singular forms of each keyword (if applicable).
            marketplace (Optional[str]): If 'UK', the resulting list will convert US keywords
                to British keywords
        Returns:
            List[str]: A cleaned-up list of keyword strings.

        """
        translator = str.maketrans("", "", string.punctuation)
        keywords = [
            keyword.lower().translate(translator)
            for keyword in self._keywords
            if isinstance(keyword, str) and keyword
        ]
        keywords = list(set(keywords))

        if is_asins:
            keywords = [asin.zfill(10) for asin in keywords]

        if singularize:
            keywords = [inflect.engine().singular_noun(keyword) or keyword for keyword in keywords]

        if marketplace == "UK":
            json_path = os.path.join(os.path.dirname(__file__), "dict", "american_to_british.json")
            with open(json_path) as file:
                dict = json.load(file)
            
            keywords = [dict.get(keyword, keyword) for keyword in keywords]

        keywords = [
            keyword for keyword in keywords if len(keyword) >= 4 and keyword not in TOP_50_COMMON_KEYWORDS
        ]

        return keywords
