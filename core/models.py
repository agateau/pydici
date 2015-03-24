# coding: utf-8
"""
Database access layer for pydici core module
@author: Aurélien Gâteau (mail@agateau.com)
@license: AGPL v3 or newer (http://www.gnu.org/licenses/agpl-3.0.html)

Some parts of Pydici require being a member of a group with access to specific
features.

To check if a user has access to a feature from Python code, use
`utils.user_has_feature()` or the `decorator.pydici_feature()` decorator.

To check for access from a template, use `{% if feature.<feature_name> %}`.
"""

from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import ugettext_lazy as _


FEATURES = sorted([
    "leads",
    "mass_staffing",
    "3rdparties",
    "management",
    "reports",
    "search",
])


class GroupFeature(models.Model):
    """Represents whether a group has access to a certain feature. If Feature
    was a model, this would be the intermediary model between Feature and Group.
    """
    group = models.ForeignKey(Group)
    feature = models.CharField(_("Feature"), max_length=80,
                               choices=[(x, x) for x in FEATURES])
    class Meta:
        unique_together = (('group', 'feature'))

    def __unicode__(self):
        return unicode(self.group) + '-' + unicode(self.feature)
