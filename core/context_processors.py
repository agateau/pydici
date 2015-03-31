from collections import defaultdict
from importlib import import_module

from django.conf import settings

from core.utils import user_has_feature


class FeatureWrapper(object):
    def __init__(self, user):
        self.user = user

    def __getitem__(self, feature):
        return user_has_feature(self.user, str(feature))

    def __contains__(self, feature):
        return bool(self[feature])


def feature(request):
    """
    Returns context variables to check if the current user has access to Pydici
    features.
    """
    if hasattr(request, 'user'):
        user = request.user
    else:
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()

    return {
        'pydici_feature': FeatureWrapper(user),
    }


_menu_templates = None


def _init_menu_templates():
    global _menu_templates
    _menu_templates = defaultdict(list)
    for app in settings.INSTALLED_APPS:
        try:
            mod = import_module(app + '.menus')
        except ImportError:
            continue
        for menu_name, template_name in mod.get_menus().items():
            _menu_templates[menu_name].append(template_name)


class MenuWrapper(object):
    def __getitem__(self, name):
        return _menu_templates.get(name)

    def __contains__(self, name):
        return bool(self[name])


def menu(request):
    if _menu_templates is None:
        _init_menu_templates()
    return {
        'pydici_menu': MenuWrapper(),
    }
