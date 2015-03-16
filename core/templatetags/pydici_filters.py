# coding:utf-8
"""
Pydici custom filters
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: AGPL v3 or newer (http://www.gnu.org/licenses/agpl-3.0.html)
"""

import re

from django import template
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.core.cache import cache

from people.models import Consultant
from leads.models import Lead
import pydici.settings

register = template.Library()

regex_template = r"""
    (?P<before>\W|^)
    {fence}
    (?P<content>([^{fence}]|{fence}\w)+)
    {fence}
    (?P<after>\W|^)
    """
# *star* text
stared_text = re.compile(
    regex_template.format(fence=r'\*'),
    re.UNICODE | re.VERBOSE)
# _underlined_ text
underlined_text = re.compile(
    regex_template.format(fence='_'),
    re.UNICODE | re.VERBOSE)
# bullet point
bullet_point = re.compile(r"\s*[*-]{1,2}[^*-]", re.UNICODE)


@register.filter
def truncate_by_chars(value, arg):
    """ Truncate words if higher than value and use "..."   """
    try:
        limit = int(arg)
        value = unicode(value)
    except ValueError:
        return value
    if len(value) >= limit:
        return value[:limit - 3] + "..."
    else:
        return value


@register.filter
def split(value, arg):
    """Split a string on "arg" and return a list"""
    return value.split(arg)


@register.filter
def to_float(value, arg=None):
    """Coerce value to float. Return unchanged value if cast fails"""
    try:
        return float(value)
    except ValueError:
        return value


@register.filter
def link_to_consultant(value, arg=None):
    """create a link to consultant if he exists
    @param value: consultant trigramme"""
    result = cache.get("link_to_consultant_%s" % value)
    if result:
        return result
    try:
        consultant = Consultant.objects.get(trigramme__iexact=value)
        if consultant.name:
            name = consultant.name
        else:
            name = value
        if consultant.subcontractor or arg == "nolink":
            result = escape(name)
        else:
            result = "<a href='%s'>%s</a>" % (reverse("people.views.consultant_home", args=[consultant.id, ]),
                                        escape(name))
        result = mark_safe(result)
        cache.set("link_to_consultant_%s" % value, result, 180)
        return mark_safe(result)
    except Consultant.DoesNotExist:
        try:
            user = User.objects.get(username=value)
            return "%s %s" % (user.first_name, user.last_name)
        except User.DoesNotExist:
            # User must exists if logged... anyways, be safe.
            return value


@register.filter
def link_to_timesheet(value, arg=None):
    """create a link to consultant timesheet if he exists
    @param value: consultant trigramme"""
    try:
        c = Consultant.objects.get(trigramme__iexact=value)
        url = "<a href='%s#tab-timesheet'>%s</a>" % (reverse("people.views.consultant_home", args=[c.id, ]),
                                        escape(_("My timesheet")))
        return mark_safe(url)
    except Consultant.DoesNotExist:
        return None


@register.filter
def link_to_staffing(value, arg=None):
    """create a link to consultant forecast staffing if he exists
    @param arg: consultant trigramme"""
    try:
        c = Consultant.objects.get(trigramme__iexact=value)
        url = "<a href='%s#tab-staffing'>%s</a>" % (reverse("people.views.consultant_home", args=[c.id, ]),
                                        escape(_("My staffing")))
        return mark_safe(url)
    except Consultant.DoesNotExist:
        return None


@register.filter
def get_admin_mail(value, arg=None):
    """Config to get admin contact"""
    if pydici.settings.ADMINS:
        return mark_safe("<a href='mailto:%s'>%s</a>" % (pydici.settings.ADMINS[0][1],
                                                         _("Mail to support")))


@register.filter
def pydici_simple_format(value, arg=None):
    """Very simple markup formating.
    Markdown and rst are too much complicated"""
    dealIds = [i[0] for i in Lead.objects.exclude(deal_id="").values_list("deal_id")]
    trigrammes = [i[0] for i in Consultant.objects.values_list("trigramme")]

    # format *word* and _word_ and look for deal ids
    value = stared_text.sub(r"\g<before><strong>\g<content></strong>\g<after>", value)
    value = underlined_text.sub(r"\g<before><em>\g<content></em>\g<after>", value)
    result = []
    inList = False  # Flag to indicate we are in a list
    for line in value.split("\n"):
        newline = []
        for word in line.split():
            if word in dealIds:
                word = u"<a href='%s'>%s</a>" % (Lead.objects.get(deal_id=word).get_absolute_url(), word)
            if word in trigrammes:
                word = u"<a href='%s'>%s</a>" % (Consultant.objects.get(trigramme=word).get_absolute_url(), word)
            newline.append(word)
        line = " ".join(newline)

        if bullet_point.match(line):
            if not inList:
                result.append(u"<ul>")
            result.append(u"<li>%s</li>" % line.strip().lstrip("*").lstrip("-"))
            inList = True
        else:
            if inList:
                result.append(u"</ul>")
            result.append(line + u"\n")
            inList = False
    value = "".join(result)

    return mark_safe(value)
