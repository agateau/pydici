# coding:utf-8
"""
Core form setup
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: AGPL v3 or newer (http://www.gnu.org/licenses/agpl-3.0.html)
"""

from django import forms
from django.core.validators import EMPTY_VALUES
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django_select2.fields import AutoModelSelect2Field


class SearchForm(forms.Form):
    search = forms.CharField(max_length=100)


class PydiciSelect2Field():
    empty_values = EMPTY_VALUES

    def security_check(self, request, *args, **kwargs):
        """Restrict access to authenticated and active users only"""
        return request.user.is_authenticated() and request.user.is_active


class UserChoices(PydiciSelect2Field, AutoModelSelect2Field):
    queryset = User.objects
    search_fields = ["username__icontains", "first_name__icontains", "last_name__icontains"]

    def get_queryset(self):
        return User.objects.filter(is_active=True)


class PydiciCrispyBaseForm(object):
    """A base form to be subclassed. Factorise common things of all pydici crispy forms"""
    def __init__(self, *args, **kwargs):
        super(PydiciCrispyBaseForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.submit = Submit("Submit", _("Save"))
        self.submit.field_classes = "btn btn-default"


class PydiciCrispyModelForm(PydiciCrispyBaseForm, forms.ModelForm):
    """pydici model forms"""
    pass

class PydiciCrispyForm(PydiciCrispyBaseForm, forms.Form):
    """pydici standard (non-model) forms"""
    pass