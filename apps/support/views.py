import logging
import os

from celery.local import PromiseProxy
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

from adsdroid.settings import DATA_EXCHANGE_LOG_FILE, LOG_DIR
from apps.ads_api.data_exchange import (
    campaign_roster,
    get_keyword_rank_from_google_sheets,
    get_profile_book_catalog,
    check_targets_and_keywords_not_updated_in_48_hours,
    rename_campaigns_standard,
    deduplicate_targets,
    get_keyword_rank_from_google_sheets,
    get_catalog,
    # update_product_own_campaigns_with_new_books,
    # clean_up_ended_campaigns
    # update_bids_for_managed,
)
from apps.ads_api.tasks import (
    update_books_eligibility,
    sync_profiles_chain,
    create_campaign_from_google_sheet,
    cleanup_managed_books_and_campaigns_for_unmanaged_profiles, turn_on_profit_mode,
    create_campaigns_task,
    sp_process_reports,
    partial_request_reports
)
from .forms import (
    CampaignRosterForm,
    ProfilesChoiceForm,
    HijackUserForm,
)

from apps.ads_api.models import (
    Book,
    Profile,
    CampaignPurpose
)
from apps.ads_api.services.keywords.cleaner_service import KeywordsCleanerService

_logger = logging.getLogger(__name__)


from apps.ads_api.adapters.amazon_ads.reports_adapter import ReportsAdapter
from apps.ads_api.constants import SpReportType, AdProductTypes, TypeIdOfReport, AdStatus, TimeUnitOfReport, \
    FormatOfReport, ServerLocation


@user_passes_test(lambda u: u.is_superuser, login_url="/404")
def hijack_user(request):
    form = HijackUserForm()
    return render(
        request,
        "support/hijack_user.html",
        {
            "form": form,
            "redirect_url": settings.LOGIN_REDIRECT_URL,
        },
    )


@user_passes_test(lambda u: u.is_superuser, login_url="/404")
def manage_fucntions(request):
    # create_campaign_from_google_sheet()
    # update_bids_for_managed()
    # get_catalog('ENTITYNZPENIQQBH6K', 'US')
    # get_keyword_rank_from_google_sheets()
    # create_campaigns_task([9, 92,93, 94, 95, 96, 97, 98], [CampaignPurpose.Product_Own])
    # cleaner = KeywordsCleanerService(keywords=["Africanization", "categorize", "test"])
    # cleaner.clean_keywords(marketplace="UK")
    # clean_up_ended_campaigns()
    partial_request_reports([45])
    # sp_process_reports()
    # update_product_own_campaigns_with_new_books()
    available_tasks = {
        sync_profiles_chain.__name__: sync_profiles_chain,
        create_campaign_from_google_sheet.__name__: create_campaign_from_google_sheet,
        get_keyword_rank_from_google_sheets.__name__: get_keyword_rank_from_google_sheets,
        campaign_roster.__name__: campaign_roster,
        get_profile_book_catalog.__name__: get_profile_book_catalog,
        turn_on_profit_mode.__name__: turn_on_profit_mode,
        check_targets_and_keywords_not_updated_in_48_hours.__name__: check_targets_and_keywords_not_updated_in_48_hours,
        update_books_eligibility.__name__: update_books_eligibility,
        rename_campaigns_standard.__name__: rename_campaigns_standard,
        deduplicate_targets.__name__: deduplicate_targets,
        cleanup_managed_books_and_campaigns_for_unmanaged_profiles.__name__:
            cleanup_managed_books_and_campaigns_for_unmanaged_profiles
    }

    forms = {
        campaign_roster.__name__: CampaignRosterForm(
            initial={"task": campaign_roster.__name__}
        ),
        get_profile_book_catalog.__name__: ProfilesChoiceForm(
            initial={"task": get_profile_book_catalog.__name__}
        ),
        turn_on_profit_mode.__name__: ProfilesChoiceForm(
            initial={"task": turn_on_profit_mode.__name__}
        ),
        rename_campaigns_standard.__name__: ProfilesChoiceForm(
            initial={"task": rename_campaigns_standard.__name__}
        ),
        deduplicate_targets.__name__: ProfilesChoiceForm(
            initial={"task": deduplicate_targets.__name__}
        )
    }

    task_started = None
    task_name = None

    if request.method == "POST":
        task_name = request.POST.get("task")

        form = forms.get(task_name)
        try:
            if form:
                form = type(form)(request.POST)
                if form.is_valid():
                    form.cleaned_data.pop("task")
                    args = form.cleaned_data

                    # checking is task is celery task or just a function
                    if isinstance(available_tasks[task_name], PromiseProxy):
                        available_tasks[task_name].delay(**args)
                    else:
                        available_tasks[task_name](**args)
            else:
                # checking is task is celery task or just a function
                if isinstance(available_tasks[task_name], PromiseProxy):
                    available_tasks[task_name].apply_async()
                else:
                    available_tasks[task_name]()

            task_started = True
        except Exception as e:
            task_started = False
            _logger.error("Get error while starting task %s, %s", task_name, e)

    return render(
        request,
        "support/manage_functions.html",
        {
            "forms": forms.values(),
            # filter tasks that don't have a form
            "tasks_without_form": [
                task for task in available_tasks.keys() if task not in forms.keys()
            ],
            "task_state": task_started,
            "task_name": task_name,
            "redirect_url": settings.LOGIN_REDIRECT_URL,
        },
    )


@user_passes_test(lambda u: u.is_superuser, login_url="/404")
def logs_view(request):
    last_bytes_size = 524288  # bytes
    with open(os.path.join(LOG_DIR, DATA_EXCHANGE_LOG_FILE), "r") as f:
        f_size = os.stat(f.name).st_size
        if f_size > last_bytes_size:
            f.seek(f_size - last_bytes_size)
            lines = reversed(f.readlines())
        else:
            lines = reversed(f.readlines())
    return render(request, "support/logs.html", {"logs": lines})
