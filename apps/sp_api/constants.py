import enum
import os

from apps.ads_api.constants import ServerLocation

MARKETPLACE_REGION = "US"
BOOK_PRODUCT_CATEGORY_ID = "283155"
BOOK_DISPLAY_ON_WEBSITE = "book_display_on_website"

RefreshToken = {
    ServerLocation.NORTH_AMERICA: os.environ.get("SP_API_REFRESH_TOKEN_NA"),
    ServerLocation.EUROPE: os.environ.get("SP_API_REFRESH_TOKEN_EU"),
    ServerLocation.FAR_EAST: os.environ.get("SP_API_REFRESH_TOKEN_AU"),
}

BaseSpApiUrls = {
    ServerLocation.NORTH_AMERICA: "https://sellingpartnerapi-na.amazon.com",
    ServerLocation.EUROPE: "https://sellingpartnerapi-eu.amazon.com",
    ServerLocation.FAR_EAST: "https://sellingpartnerapi-fe.amazon.com",
}

MARKETPLACES = {
    "CA": "A2EUQ1WTGCTBG2",
    "US": "ATVPDKIKX0DER",
    "MX": "A1AM78C64UM0Y8",
    "BR": "A2Q3Y263D00KWC",
    "ES": "A1RKKUPIHCS9HS",
    "UK": "A1F83G8C2ARO7P",
    "FR": "A13V1IB3VIYZZH",
    "NL": "A1805IZSGTT6HS",
    "DE": "A1PA6795UKMFR9",
    "IT": "APJ6JRA9NG5V4",
    "SE": "A2NODRKZP88ZB9",
    "PL": "A1C3SOZRARQ6R3",
    "EG": "ARBP9OOSHTCHU",
    "TR": "A33AVAJ2PDY3EV",
    "AE": "A2VIGQ35RCS4UG",
    "IN": "A21TJRUUN4KGV",
    "SG": "A19VAU5U5O7RUS",
    "AU": "A39IBJ37TRP1C6",
    "JP": "A1VC38T7YXB528",
}

ROW_LIST = [
    "title",
    "author",
    "ASIN",
    "publication_date",
    "book_format",
    "price",
    "sales_rank",
    "",
    "reviews",
    "length",
    "",
    "",
    "category",
    "search_term",
    "qualifies",
]

SHEETS_API_THROTLING_SEC = 150

THROTTLING_HTTP_CODE = 429

# Book info constants:

# Ref: https://kdp.amazon.com/en_US/help/topic/G201645450
EU_VAT_PERCENTAGES = {
    "DE": 0.07,
    "FR": 0.055,
    "IT": 0.04,
    "ES": 0.04,
    "NL": 0.09,
}

MAX_SHORT_BOOK_LENGTH = 110

RATES = {
    # https://kdp.amazon.com/en_US/help/topic/G201834340
    "Paperback": {
        "Black": {
            "Short": {
                "Fixed": {
                    "US": 2.15,
                    "CA": 2.82,
                    "UK": 1.70,
                    "DE": 1.90,
                    "FR": 1.90,
                    "IT": 1.90,
                    "ES": 1.90,
                    "AU": 4.49,
                    "JP": 400,
                },
            },
            "Long": {
                "Fixed": {
                    "US": 0.85,
                    "CA": 1.11,
                    "UK": 0.70,
                    "DE": 0.60,
                    "FR": 0.60,
                    "IT": 0.60,
                    "ES": 0.60,
                    "AU": 2.17,
                    "JP": 175,
                },
                "Per_Page": {
                    "US": 0.012,
                    "CA": 0.016,
                    "UK": 0.010,
                    "DE": 0.012,
                    "FR": 0.012,
                    "IT": 0.012,
                    "ES": 0.012,
                    "AU": 0.0215,
                    "JP": 2,
                },
            },
        },
        "Colour": {
            "Fixed": {
                "US": 0.85,
                "CA": 1.11,
                "UK": 0.70,
                "DE": 0.60,
                "FR": 0.60,
                "IT": 0.60,
                "ES": 0.60,
            },
            "Per_Page": {
                "US": 0.036,
                "CA": 0.047,
                "UK": 0.025,
                "DE": 0.031,
                "FR": 0.031,
                "IT": 0.031,
                "ES": 0.031,
            },
        },
    },
    # https://kdp.amazon.com/en_US/help/topic/GHT976ZKSKUXBB6H
    "Hardcover": {
        "Black": {
            "Short": {
                "Fixed": {
                    "US": 6.80,
                    "UK": 5.80,
                    "DE": 5.80,
                    "FR": 5.80,
                    "IT": 5.80,
                    "ES": 5.80,
                },
            },
            "Long": {
                "Fixed": {
                    "US": 5.50,
                    "UK": 4.00,
                    "DE": 4.50,
                    "FR": 4.50,
                    "IT": 4.50,
                    "ES": 4.50,
                },
                "Per_Page": {
                    "US": 0.012,
                    "UK": 0.010,
                    "DE": 0.012,
                    "FR": 0.012,
                    "IT": 0.012,
                    "ES": 0.012,
                },
            },
        },
        "Colour": {
            "Fixed": {
                "US": 5.50,
                "UK": 4.00,
                "DE": 4.50,
                "FR": 4.50,
                "IT": 4.50,
                "ES": 4.50,
            },
            "Per_Page": {
                "US": 0.070,
                "UK": 0.045,
                "DE": 0.060,
                "FR": 0.060,
                "IT": 0.060,
                "ES": 0.060,
            },
        },
    },
    "Kindle": {
        # Ref: https://kdp.amazon.com/en_US/help/topic/G200634560
        "higher_royalty_threshold": {
            "US": 2.99,
            "CA": 2.99,
            "BR": 5.99,
            "UK": 1.77,
            "DE": 2.51,
            "FR": 2.55,
            "IT": 2.20,
            "ES": 2.59,
            "NL": 2.47,
            "JP": 250,
            "MX": 34.99,
            "AU": 3.99,
            "IN": 99,
        },
        # per MB
        "Delivery": {
            "US": 0.15,
            "CA": 0.15,
            "BR": 0.30,
            "UK": 0.10,
            "DE": 0.12,
            "FR": 0.12,
            "ES": 0.12,
            "IT": 0.12,
            "NL": 0.12,
            "JP": 1,
            "MX": 1,
            "AU": 0.15,
            "IN": 7,
        },
    },
}

classificationIds = {
    "US": {"Kindle": 133141011, "Books": 1000},
    "CA": {"Kindle": 2972706011, "Books": 927726},
    "UK": {"Kindle": 341678031, "Books": 1025612},
    "AU": {"Kindle": 2490360051, "Books": 4851627051},
    "DE": {"Kindle": 530485031, "Books": 541686},
    "ES": {"Kindle": 818938031, "Books": 599365031},
    "FR": {"Kindle": 672109031, "Books": 301130},
    "IT": {"Kindle": 818939031, "Books": 411664031},
}

MAX_BOOK_BSR_TRESHOLD: int = 100_000
