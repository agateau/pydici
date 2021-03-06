# coding: utf-8

"""
Helper module that factorize some code that would not be
appropriate to live in Lead models or view
@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license: AGPL v3 or newer (http://www.gnu.org/licenses/agpl-3.0.html)
"""
from django.utils.translation import ugettext
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, ContentType
from django.utils.encoding import force_unicode

from staffing.models import Mission
from core.utils import send_lead_mail


def postSaveLead(request, lead, updated_fields):
    mail = False
    if lead.send_email:
        mail = True
        lead.send_email = False

    lead.save()

    # Log it
    LogEntry.objects.log_action(
        user_id         = request.user.pk,
        content_type_id = ContentType.objects.get_for_model(lead).pk,
        object_id       = lead.pk,
        object_repr     = force_unicode(lead),
        action_flag     = ADDITION,
        change_message  = ", ".join(updated_fields),
    )

    if mail:
        try:
            fromAddr = request.user.email or "noreply@noreply.com"
            send_lead_mail(lead, request, fromAddr=fromAddr,
                           fromName="%s %s" % (request.user.first_name, request.user.last_name))
            messages.add_message(request, messages.INFO, ugettext("Lead sent to business mailing list"))
        except Exception, e:
            messages.add_message(request, messages.ERROR, ugettext("Failed to send mail: %s") % e)

    # Create or update mission  if needed
    if lead.mission_set.count() == 0:
        if lead.state in ("OFFER_SENT", "NEGOTIATION", "WON"):
            mission = Mission(lead=lead)
            mission.price = lead.sales  # Initialise with lead price
            mission.subsidiary = lead.subsidiary
            mission.responsible = lead.responsible
            mission.save()
            # Create default staffing
            mission.create_default_staffing()
            messages.add_message(request, messages.INFO, ugettext("A mission has been initialized for this lead."))

    for mission in lead.mission_set.all():
        if mission.subsidiary != lead.subsidiary:
            mission.subsidiary = lead.subsidiary
            mission.save()
        if lead.state == "WON":
            mission.probability = 100
            mission.active = True
            mission.save()
            messages.add_message(request, messages.INFO, ugettext("Mission's probability has been set to 100%"))
        elif lead.state in ("LOST", "FORGIVEN", "SLEEPING"):
            mission.probability = 0
            mission.active = False
            mission.save()
            messages.add_message(request, messages.INFO, ugettext("According mission has been archived"))
