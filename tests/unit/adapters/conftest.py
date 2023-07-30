from collections import namedtuple

import pytest


@pytest.fixture(scope="module")
def google_books_api_response():
    response_text = """
        {
         "kind": "books#volumes",
         "totalItems": 9,
         "items": [
           {
             "kind": "books#volume",
             "id": "qb8fzgEACAAJ",
             "etag": "17atbaTAQHc",
             "selfLink": "https://www.googleapis.com/books/v1/volumes/qb8fzgEACAAJ",
             "volumeInfo": {
               "title": "Campfire Stories for Kids Part II",
               "subtitle": "A Scary Ghost, Witch, and Goblin Tales Collection to Tell in the Dark: 20 Scary and Funny Short Horror Stories for Children While Camping Or for Sleepovers",
               "authors": [
                 "Johnny Nelson"
               ],
               "publishedDate": "2020-12-20",
               "description": "Offer your kids the spooky story experience they have been craving. Campfire Stories for Kids Part II: A Scary Ghost, Witch and Goblin Tales Collection to Tell in the Dark is a unique title and a wonderful book to add to your growing collection. Your children will love this pick, as it trusts them to handle a few scares. You will love the peace of mind in knowing that your family is consuming mild content, safe for the enjoyment of even the youngest members. Have you been looking for a way to bring the family together during stormy nights? Have you been looking for something to read by the campfire during your next vacation? This book is full of thrilling tales that were written to keep children invested in the story. As your kid reads through these stories, their vocabulary will grow. Many of these chapters also reinforce the morals that you have already taught your little ones. Have you been looking for a book that suits your child's tastes? This book is full of young main characters trying to work their way out of sticky situations. Sometimes the good guy wins, and sometimes they go back to the drawing table. Watch your child's eyes light up as they find their favorite chapter. This title is perfect for those just learning to read but would also make a wonderful nighttime wind down. Finding a routine during the evening is an essential part of designing a peaceful bedtime. Has your child discovered the genres and stories they love, yet? Offer your kid a chance to explore their taste by surprising them with this book. There is something for everyone within these pages, and your little one will appreciate the variety. Your child can read these stories on their own, or they could follow along as you read to them. No matter how you use storybooks, literature is a vital part of childhood development. There are so many wonderful reasons to buy your child a storybook. Don't miss out on the opportunity to find literature that your little one is going to love. Buy this book now for adventures that kick starts imaginations and maybe even provide a little scare. Know that your child is reading age-appropriate stories, even if they are a little frightening. Follow ghosts, witches, sirens, monsters, and more, right into the abyss. You might even find yourself slipping into a parallel universe if you aren't careful. This book is overflowing with themes and characters that children love. This book does not contain gore or obscene language. Feeding the little horror fan in your life without exposing them to violent material, can be easier said than done. Campfire Stories for Kids: A Scary Ghost, Witch, and Goblin Tales Collection to Tell in the Dark was written with younger readers in mind. These stories are full of fascinating characters meant to take your child on a journey from the comfort of their own home. Read about spooky spirits and malevolent entities meant to thrill you and your family. These stories are tense enough to offer thrills, but they also include moral lessons and humor. Your child will return to these tales again and again. Have you been looking for a way to make bedtime easier? Give this book a try. Bond with your kids as they learn to read or follow along with your voice.",
               "industryIdentifiers": [
                 {
                   "type": "ISBN_13",
                   "identifier": "9798584378882"
                 }
               ],
               "readingModes": {
                 "text": false,
                 "image": false
               },
               "pageCount": 144,
               "printType": "BOOK",
               "maturityRating": "NOT_MATURE",
               "allowAnonLogging": false,
               "contentVersion": "preview-1.0.0",
               "panelizationSummary": {
                 "containsEpubBubbles": false,
                 "containsImageBubbles": false
               },
               "imageLinks": {
                 "smallThumbnail": "http://books.google.com/books/content?id=qb8fzgEACAAJ&printsec=frontcover&img=1&zoom=5&source=gbs_api",
                 "thumbnail": "http://books.google.com/books/content?id=qb8fzgEACAAJ&printsec=frontcover&img=1&zoom=1&source=gbs_api"
               },
               "language": "en",
               "previewLink": "http://books.google.com/books?id=qb8fzgEACAAJ&dq=9798584378882&hl=&cd=1&source=gbs_api",
               "infoLink": "http://books.google.com/books?id=qb8fzgEACAAJ&dq=9798584378882&hl=&source=gbs_api",
               "canonicalVolumeLink": "https://books.google.com/books/about/Campfire_Stories_for_Kids_Part_II.html?hl=&id=qb8fzgEACAAJ"
             },
             "saleInfo": {
               "country": "US",
               "saleability": "NOT_FOR_SALE",
               "isEbook": false
             },
             "accessInfo": {
               "country": "US",
               "viewability": "NO_PAGES",
               "embeddable": false,
               "publicDomain": false,
               "textToSpeechPermission": "ALLOWED",
               "epub": {
                 "isAvailable": false
               },
               "pdf": {
                 "isAvailable": false
               },
               "webReaderLink": "http://play.google.com/books/reader?id=qb8fzgEACAAJ&hl=&source=gbs_api",
               "accessViewStatus": "NONE",
               "quoteSharingAllowed": false
             },
             "searchInfo": {
               "textSnippet": "&quot;In Campfire Stories for Kids: A Scary Ghost, Witch and Goblin Tales Collection to Tell in the Dark, the reader will find a fun collection of magical and spooky tales to delight your children."
             }
           },
           {
             "kind": "books#volume",
             "id": "qMBHxwEACAAJ",
             "etag": "g1B6X1xI2s8",
             "selfLink": "https://www.googleapis.com/books/v1/volumes/qMBHxwEACAAJ",
             "volumeInfo": {
               "title": "Campfire Stories for Kids",
               "subtitle": "A Story Collection of Scary and Humorous Camp Fire Tales",
               "authors": [
                 "Drake Quinn"
               ],
               "publishedDate": "2019-05-30",
               "description": "Do you have fond memories of being told stories around the campfire? Classic campfire stories are those which have been passed down from generation to generation. This collection of twenty-one stories includes some urban legends, including the ghost of the bloody finger and the girl in the white dress. You'll also find some new stories that will make you laugh out loud, or have you sitting on the edge of your seat wondering how it will end. Every one of these campfire stories and tales are great for: sharing around the campfire kids who love spooky ghost stories and funny tales reading aloud or listening to on a dark nights creating marvellous memories Laughter and being a little scared together are great way to bond together around the camp fire. Scroll up to grab your copy of Campfire Stories for Kids and start reading them or sharing them around the campfire today!",
               "industryIdentifiers": [
                 {
                   "type": "ISBN_10",
                   "identifier": "1070876372"
                 },
                 {
                   "type": "ISBN_13",
                   "identifier": "9781070876375"
                 }
               ],
               "readingModes": {
                 "text": false,
                 "image": false
               },
               "pageCount": 144,
               "printType": "BOOK",
               "maturityRating": "NOT_MATURE",
               "allowAnonLogging": false,
               "contentVersion": "preview-1.0.0",
               "panelizationSummary": {
                 "containsEpubBubbles": false,
                 "containsImageBubbles": false
               },
               "language": "en",
               "previewLink": "http://books.google.com/books?id=qMBHxwEACAAJ&dq=9798584378882&hl=&cd=2&source=gbs_api",
               "infoLink": "http://books.google.com/books?id=qMBHxwEACAAJ&dq=9798584378882&hl=&source=gbs_api",
               "canonicalVolumeLink": "https://books.google.com/books/about/Campfire_Stories_for_Kids.html?hl=&id=qMBHxwEACAAJ"
             },
             "saleInfo": {
               "country": "US",
               "saleability": "NOT_FOR_SALE",
               "isEbook": false
             },
             "accessInfo": {
               "country": "US",
               "viewability": "NO_PAGES",
               "embeddable": false,
               "publicDomain": false,
               "textToSpeechPermission": "ALLOWED",
               "epub": {
                 "isAvailable": false
               },
               "pdf": {
                 "isAvailable": false
               },
               "webReaderLink": "http://play.google.com/books/reader?id=qMBHxwEACAAJ&hl=&source=gbs_api",
               "accessViewStatus": "NONE",
               "quoteSharingAllowed": false
             },
             "searchInfo": {
               "textSnippet": "Classic campfire stories are those which have been passed down from generation to generation. This collection of twenty-one stories includes some urban legends, including the ghost of the bloody finger and the girl in the white dress."
             }
           }
         ]
       }
   
       """
    Response = namedtuple(
        "Response",
        [
            "text",
        ],
    )
    return Response(text=response_text)


@pytest.fixture(scope="module")
def response_with_no_results():
    response_text = """
        {
          "kind": "books#volumes",
          "totalItems": 0
        }
        """
    Response = namedtuple(
        "Response",
        [
            "text",
        ],
    )
    return Response(text=response_text)


@pytest.fixture
def profile_info_response():
    return {
        "csrfToken": "g2YA7Khvw+g9eIfBVStbas3R1jlyRA7gjswiY3emddINAAAAAQAAAABj92nZcmF3AAAAAIwO8jooET7XVH8cQ/E9xQ==",
        "csrfData": "amzn.advertising.789c333434373434323434050008d801c5",
        "clientId": "amzn.advertising.789c333434373434323434050008d801c5",
        "entityId": "ENTITY142FXA60IODV6",
        "marketplaceId": "A1F83G8C2ARO7P",
        "advertisingApiEndpoint": "https://advertising.amazon.co.uk/a9g-api",
        "isSpoofing": False,
        "consoleId": "A1HCRISWWMZWXO",
        "locale": "en_GB",
        "sdftvUserType": None,
    }


@pytest.fixture
def single_book_response():
    return {
        "asin": "B0BK74FYBM",
        "name": "A Mark Of Imperfection: A Black Beacons Murder Mystery (DCI Evan Warlow Crime Thriller Book 6)",
        "asinUrl": "https://www.amazon.co.uk/Mark-Imperfection-Beacons-Mystery-Thriller-ebook/dp/B0BK74FYBM",
        "imageUrl": "https://m.media-amazon.com/images/I/51l9wtBCwJL._SS60_.jpg",
        "availability": "IN_STOCK",
        "bookBindingInformation": "Kindle Edition",
        "variations": [],
        "titleAuthorityParentAsin": "B0BK75Z58G",
        "customerReview": {
            "rating": {
                "displayString": "4.7 out of 5 stars",
                "fullStarCount": 4,
                "hasHalfStar": True,
                "value": 4.7,
            },
            "reviewCount": {"displayString": "1,726", "value": 1726},
            "reviewUrl": "https://www.amazon.co.uk/product-reviews/B0BK74FYBM",
        },
        "price": {
            "type": "UNKNOWN",
            "valueType": "SINGLE",
            "currency": "GBP",
            "min": 3.99,
            "max": 3.99,
        },
        "prices": [
            {
                "type": "UNKNOWN",
                "valueType": "SINGLE",
                "currency": "GBP",
                "min": 3.99,
                "max": 3.99,
            },
            {
                "type": "UNKNOWN",
                "valueType": "SINGLE",
                "currency": "GBP",
                "min": 3.99,
                "max": 9.99,
            },
        ],
        "eligibilityStatus": "ELIGIBLE",
        "ineligibilityReasons": [],
        "ineligibilityCodes": [],
        "eligibleWithWarningReasons": [],
        "eligibleWithWarningCodes": [],
        "asinEligibility": {"ineligibilityReasons": [], "ineligibilityCodes": []},
        "adEligibility": {"ineligibilityReasons": [], "ineligibilityCodes": []},
    }


@pytest.fixture
def book_catalog_response(single_book_response):
    return [single_book_response, single_book_response]


def pending_report_response():
    return {
        "configuration": {
            "adProduct": "SPONSORED_PRODUCTS",
            "columns": [
                "impressions",
                "cost",
                "purchases30d",
                "clicks",
                "sales30d",
                "campaignId",
                "unitsSoldClicks30d",
                "kindleEditionNormalizedPagesRoyalties14d",
            ],
            "filters": [{"field": "campaignStatus", "values": ["ENABLED"]}],
            "format": "GZIP_JSON",
            "groupBy": ["campaign"],
            "reportTypeId": "spCampaigns",
            "timeUnit": "DAILY",
        },
        "createdAt": "2023-02-28T16:00:07.546Z",
        "endDate": "2023-02-28",
        "failureReason": None,
        "fileSize": None,
        "generatedAt": None,
        "name": None,
        "reportId": "942c4d47-a33f-425d-8fa7-ef9a691fc8b3",
        "startDate": "2023-02-28",
        "status": "PENDING",
        "updatedAt": "2023-02-28T16:00:07.546Z",
        "url": None,
        "urlExpiresAt": None,
    }
