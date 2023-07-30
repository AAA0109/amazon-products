import json
from typing import Optional

from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse

from apps.openai_api.filters.avatar_description_filter import AvatarDescriptionFilter
from apps.openai_api.suggesters.title_keywords_suggester import TitleKeywordsSuggester
from apps.openai_api.suggesters.title_asins_suggester import (
    TitleAsinsSuggester,
)


@user_passes_test(test_func=lambda u: u.is_superuser, login_url="/404")
def suggest_keywords(request) -> JsonResponse:
    title: Optional[str] = request.POST.get("title")
    if not title:
        return JsonResponse({"error": "title is required"}, status=400)

    keywords: list[str] = TitleKeywordsSuggester.suggest_keywords(title=title)
    data: dict = {"date": keywords}
    return JsonResponse(data=data)


@user_passes_test(test_func=lambda u: u.is_superuser, login_url="/404")
def filter_keywords(request) -> JsonResponse:
    body: dict = json.loads(request.body.decode("utf-8"))
    required_parameters: list[str] = ["title", "avatar_description", "keywords_to_filter"]

    avatar_description, keywords_to_filter, title = (
        body.get("avatar_description"),
        body.get("keywords_to_filter"),
        body.get("title"),
    )

    if not avatar_description or not keywords_to_filter or not title:
        nonexistent_params = []
        for required_param in body.keys():
            if required_param not in required_parameters:
                nonexistent_params.append(required_param)
        return JsonResponse(data={"error": f"Some parameters are missing: {nonexistent_params}"}, status=400)

    keywords: list[str] = AvatarDescriptionFilter.filter(
        book_title=title,
        avatar_description=avatar_description,
        keywords_to_filter=keywords_to_filter,
    )
    data: dict = {"date": keywords}
    return JsonResponse(data=data)


@user_passes_test(test_func=lambda u: u.is_superuser, login_url="/404")
def suggest_negatives(request) -> JsonResponse:
    body: dict = json.loads(request.body.decode("utf-8"))
    required_parameters: list[str] = ["book_title", "title2asin_map"]

    book_title: Optional[str] = body.get("book_title")
    title2asin_map: Optional[dict] = body.get("title2asin_map")

    if not book_title or not title2asin_map:
        nonexistent_params = []
        for required_param in body.keys():
            if required_param not in required_parameters:
                nonexistent_params.append(required_param)
        return JsonResponse(data={"error": f"Some parameters are missing: {nonexistent_params}"}, status=400)

    asins = TitleAsinsSuggester.suggest_asins(
        book_title=book_title, title2asin_map=title2asin_map
    )
    data: dict = {"date": asins}
    return JsonResponse(data=data)
