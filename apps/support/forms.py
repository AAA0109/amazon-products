from django import forms
from django.utils.functional import lazy

from apps.ads_api.repositories.profile_repository import ProfileRepository
from apps.users.models import CustomUser


class HijackUserForm(forms.Form):
    user_pk = forms.ModelChoiceField(queryset=CustomUser.objects.order_by("email"), label="User to impersonate")


class BaseTaskForm(forms.Form):
    task = forms.CharField(
        max_length=99,
        label="task",
        widget=forms.HiddenInput(),
        required=False,
    )


class CampaignRosterForm(BaseTaskForm):
    asin = forms.CharField(max_length=99, label="asin", widget=forms.TextInput(attrs={"class": "form-control"}))
    country_code = forms.CharField(
        max_length=99, label="country code", widget=forms.TextInput(attrs={"class": "form-control"})
    )


def _profile_choises():
    return [(p.id, str(p)) for p in ProfileRepository.get_ordered_by("nickname")]


class ProfilesChoiceForm(BaseTaskForm):
    profile_ids = forms.MultipleChoiceField(choices=lazy(_profile_choises, list), widget=forms.SelectMultiple(attrs={"style": "height: 350px"}))
