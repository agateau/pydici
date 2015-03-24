# coding: utf-8
"""
Pydici views decorators
@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license: AGPL v3 or newer (http://www.gnu.org/licenses/agpl-3.0.html)
"""

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import resolve_url
from django.utils.decorators import method_decorator

from core.utils import user_has_feature


def pydici_non_public(function=None):
    """
    Decorator for views that restrict access to "internal" users. For now
    it relies on the staff user flag and is mostly used to allow external people like
    subcontractors to access only to homepage and timesheet page
    """
    actual_decorator = user_passes_test(lambda u: u.is_staff, login_url=None)
    if function:
        return actual_decorator(function)
    return actual_decorator


class PydiciNonPublicdMixin(object):
    @method_decorator(pydici_non_public)
    def dispatch(self, request, *args, **kwargs):
        return super(PydiciNonPublicdMixin, self).dispatch(request, *args, **kwargs)


def pydici_feature(feature, login_url=None):
    """
    Decorator for views which require users to have access to `feature`.
    """
    return user_passes_test(lambda u: user_has_feature(u, feature), login_url=login_url)


class PydiciFeatureMixin(object):
    """
    Decorator to check feature access for class-based views.

    Usage:

        class MyView(PydiciFeatureMixin, UpdateView):
            pydici_feature = "search"
    """
    def dispatch(self, request, *args, **kwargs):
        if not user_has_feature(request.user, self.pydici_feature):
            resolved_login_url = resolve_url(settings.LOGIN_URL)
            path = request.get_full_path()
            return redirect_to_login(path, resolved_login_url, REDIRECT_FIELD_NAME)
        return super(PydiciFeatureMixin, self).dispatch(request, *args, **kwargs)
