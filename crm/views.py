# coding: utf-8
"""
Pydici crm views. Http request are processed here.
@author: Sébastien Renard (sebastien.renard@digitalfox.org)
@license: AGPL v3 or newer (http://www.gnu.org/licenses/agpl-3.0.html)
"""

import json
from datetime import date, timedelta

from django.shortcuts import render
from django.db.models import Sum, Min
from django.views.decorators.cache import cache_page
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import DetailView, ListView
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect
from django.core import urlresolvers
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required


from crm.models import Company, Client, ClientOrganisation, Contact, AdministrativeContact, MissionContact, BusinessBroker
from crm.forms import ClientForm, ClientOrganisationForm, CompanyForm, ContactForm, MissionContactForm, AdministrativeContactForm, BusinessBrokerForm
from staffing.models import Timesheet
from people.models import Consultant
from leads.models import Lead
from core.decorator import pydici_non_public, pydici_feature, PydiciNonPublicdMixin, PydiciFeatureMixin
from core.utils import sortedValues, previousMonth, COLORS
from billing.models import ClientBill


class ContactReturnToMixin(object):
    """Mixin class to return to contact detail if return_to args is not provided"""
    def get_success_url(self):
        if self.model in (MissionContact, BusinessBroker):
            target = self.object.contact.id
        else:
            target = self.object.id
        return self.request.GET.get('return_to', False) or urlresolvers.reverse_lazy("contact_detail", args=[target, ])


class ThirdPartyMixin(PydiciFeatureMixin):
    pydici_feature = "3rdparties"


class FeatureContactsWriteMixin(PydiciFeatureMixin):
    pydici_feature = { "3rdparties", "contacts_write" }


class ContactCreate(PydiciNonPublicdMixin, ThirdPartyMixin, ContactReturnToMixin, CreateView):
    model = Contact
    template_name = "core/form.html"
    form_class = ContactForm

    def get_initial(self):
        try:
            defaultPointOfContact = Consultant.objects.get(trigramme=self.request.user.username.upper())
            return { 'contact_points': [defaultPointOfContact,]}
        except Consultant.DoesNotExist:
            return {}


class ContactUpdate(PydiciNonPublicdMixin, ThirdPartyMixin, ContactReturnToMixin, UpdateView):
    model = Contact
    template_name = "core/form.html"
    form_class = ContactForm


class ContactDelete(PydiciNonPublicdMixin, FeatureContactsWriteMixin, DeleteView):
    model = Contact
    template_name = "core/delete.html"
    form_class = ContactForm
    success_url = urlresolvers.reverse_lazy("contact_list")

    def form_valid(self, form):
        messages.add_message(self.request, messages.INFO, _("Contact removed successfully"))
        return super(ContactDelete, self).form_valid(form)

    @method_decorator(permission_required("crm.delete_contact"))
    def dispatch(self, *args, **kwargs):
        return super(ContactDelete, self).dispatch(*args, **kwargs)


class ContactDetail(PydiciNonPublicdMixin, ThirdPartyMixin, DetailView):
    model = Contact


class ContactList(PydiciNonPublicdMixin, ThirdPartyMixin, ListView):
    model = Contact


class MissionContactCreate(PydiciNonPublicdMixin, FeatureContactsWriteMixin, ContactReturnToMixin, CreateView):
    model = MissionContact
    template_name = "core/form.html"
    form_class = MissionContactForm


class MissionContactUpdate(PydiciNonPublicdMixin, FeatureContactsWriteMixin, ContactReturnToMixin, UpdateView):
    model = MissionContact
    template_name = "core/form.html"
    form_class = MissionContactForm


class BusinessBrokerCreate(PydiciNonPublicdMixin, FeatureContactsWriteMixin, ContactReturnToMixin, CreateView):
    model = BusinessBroker
    template_name = "core/form.html"
    form_class = BusinessBrokerForm


class BusinessBrokerUpdate(PydiciNonPublicdMixin, FeatureContactsWriteMixin, ContactReturnToMixin, UpdateView):
    model = BusinessBroker
    template_name = "core/form.html"
    form_class = BusinessBrokerForm


class AdministrativeContactCreate(PydiciNonPublicdMixin, FeatureContactsWriteMixin, CreateView):
    model = AdministrativeContact
    template_name = "core/form.html"
    form_class = AdministrativeContactForm

    def get_initial(self):
        return {'company': self.request.GET.get("company")}

    def get_success_url(self):
        return self.request.GET.get('return_to', False) or urlresolvers.reverse_lazy("company_detail", args=[self.object.company.id, ])


class AdministrativeContactUpdate(PydiciNonPublicdMixin, FeatureContactsWriteMixin, UpdateView):
    model = AdministrativeContact
    template_name = "core/form.html"
    form_class = AdministrativeContactForm

    def get_success_url(self):
        return self.request.GET.get('return_to', False) or urlresolvers.reverse_lazy("company_detail", args=[self.object.company.id, ])


@pydici_non_public
@pydici_feature("3rdparties")
def client(request, client_id=None):
    """Client creation or modification"""
    client = None
    try:
        if client_id:
            client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        pass

    if request.method == "POST":
        if client:
            form = ClientForm(request.POST, instance=client)
        else:
            form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            client.save()
            return HttpResponseRedirect(urlresolvers.reverse("crm.views.company_detail", args=[client.organisation.company.id]))
    else:
        if client:
            form = ClientForm(instance=client)  # A form that edit current client
        else:
            form = ClientForm()  # An unbound form

    return render(request, "crm/client.html", {"client": client,
                                               "form": form,
                                               "user": request.user})


@pydici_non_public
@pydici_feature("3rdparties")
def clientOrganisation(request, client_organisation_id=None):
    """Client creation or modification"""
    clientOrganisation = None
    try:
        if client_organisation_id:
            clientOrganisation = ClientOrganisation.objects.get(id=client_organisation_id)
    except ClientOrganisation.DoesNotExist:
        pass

    if request.method == "POST":
        if client:
            form = ClientOrganisationForm(request.POST, instance=clientOrganisation)
        else:
            form = ClientOrganisationForm(request.POST)
        if form.is_valid():
            clientOrganisation = form.save()
            clientOrganisation.save()
            return HttpResponseRedirect(urlresolvers.reverse("crm.views.company_detail", args=[clientOrganisation.company.id]))
    else:
        if clientOrganisation:
            form = ClientOrganisationForm(instance=clientOrganisation)  # A form that edit current client organisation
        else:
            form = ClientOrganisationForm()  # An unbound form

    return render(request, "crm/client_organisation.html", {"client_organisation": clientOrganisation,
                                                            "form": form,
                                                            "user": request.user})


@pydici_non_public
@pydici_feature("3rdparties")
def company(request, company_id=None):
    """Client creation or modification"""
    company = None
    try:
        if company_id:
            company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        pass

    if request.method == "POST":
        if company:
            form = CompanyForm(request.POST, instance=company)
        else:
            form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save()
            company.save()
            return HttpResponseRedirect(urlresolvers.reverse("crm.views.company_detail", args=[company.id]))
    else:
        if company:
            form = CompanyForm(instance=company)  # A form that edit current company
        else:
            form = CompanyForm()  # An unbound form

    return render(request, "crm/clientcompany.html", {"company": company,
                                                      "form": form,
                                                      "user": request.user})


@pydici_non_public
@pydici_feature("3rdparties")
def company_detail(request, company_id):
    """Home page of client company"""

    company = Company.objects.get(id=company_id)

    # Find leads of this company
    leads = Lead.objects.filter(client__organisation__company=company).select_related().prefetch_related("clientbill_set")
    leads = leads.order_by("client", "state", "start_date")

    # Find consultant that work (=declare timesheet) for this company
    consultants = [s.consultant for s in Timesheet.objects.filter(mission__lead__client__organisation__company=company).select_related("consultant")]
    consultants = list(set(consultants))  # Distinct

    companies = Company.objects.filter(clientorganisation__client__id__isnull=False).distinct()

    return render(request, "crm/clientcompany_detail.html",
                  {"company": company,
                   "leads": leads,
                   "consultants": consultants,
                   "business_contacts": Contact.objects.filter(client__organisation__company=company).distinct(),
                   "mission_contacts": Contact.objects.filter(missioncontact__company=company).distinct(),
                   "administrative_contacts": AdministrativeContact.objects.filter(company=company),
                   "clients": Client.objects.filter(organisation__company=company).select_related(),
                   "companies": companies})


@pydici_non_public
@pydici_feature("3rdparties")
def company_list(request):
    """Client company list"""
    companies = Company.objects.filter(clientorganisation__client__id__isnull=False).distinct()
    return render(request, "crm/clientcompany_list.html",
                  {"companies": list(companies)})


@pydici_non_public
@pydici_feature("3rdparties")
@cache_page(60 * 60 * 24)
def graph_company_sales_jqp(request, onlyLastYear=False):
    """Sales repartition per company"""
    graph_data = []
    labels = []
    small_clients_amount = 0
    minDate = ClientBill.objects.aggregate(Min("creation_date")).values()[0]
    if onlyLastYear:
        data = ClientBill.objects.filter(creation_date__gt=(date.today() - timedelta(365)))
    else:
        data = ClientBill.objects.all()
    data = data.values("lead__client__organisation__company__name")
    data = data.order_by("lead__client__organisation__company").annotate(Sum("amount"))
    data = data.order_by("amount__sum").reverse()
    small_clients = data[8:]
    data = data[0:8]
    for i in data:
        graph_data.append([i["lead__client__organisation__company__name"], float(i["amount__sum"])])
    # If there are more than 8 clients, we aggregate all the "small clients" under "Others"
    if len(small_clients) > 0:
        for i in small_clients:
            small_clients_amount += float(i["amount__sum"])
        graph_data.append([_("Others"), small_clients_amount])
    total = sum([i[1] for i in graph_data])
    for company, amount in graph_data:
        labels.append(u"%d k€ (%d%%)" % (amount / 1000, 100 * amount / total))

    if sum(graph_data, []):  # Test if list contains other things that empty lists
        graph_data = json.dumps([graph_data, ])
    else:
        # If graph_data is only a bunch of emty list, set it to empty list to
        # disable graph. Avoid jqplot infinite loop with some poor browsers
        graph_data = json.dumps([[None]])
    return render(request, "crm/graph_company_sales_jqp.html",
                  {"graph_data": graph_data,
                   "series_colors": COLORS,
                   "only_last_year": onlyLastYear,
                   "min_date": minDate,
                   "labels": json.dumps(labels),
                   "user": request.user})


@pydici_non_public
@pydici_feature("3rdparties")
@cache_page(60 * 60)
def graph_company_business_activity_jqp(request, company_id):
    """Business activity (leads and bills) for a company
    @todo: extend this graph to multiple companies"""
    graph_data = []
    billsData = dict()
    lostLeadsData = dict()
    currentLeadsData = dict()
    wonLeadsData = dict()
    minDate = date.today()
    company = Company.objects.get(id=company_id)

    for bill in ClientBill.objects.filter(lead__client__organisation__company=company):
        kdate = bill.creation_date.replace(day=1)
        if kdate in billsData:
            billsData[kdate] += int(float(bill.amount) / 1000)
        else:
            billsData[kdate] = int(float(bill.amount) / 1000)

    for lead in Lead.objects.filter(client__organisation__company=company):
        kdate = lead.creation_date.date().replace(day=1)
        for data in (lostLeadsData, wonLeadsData, currentLeadsData, billsData):
            data[kdate] = data.get(kdate, 0)  # Default to 0 to avoid stacking weirdness in graph
        if lead.state == "WON":
            wonLeadsData[kdate] += 1
        elif lead.state in ("LOST", "FORGIVEN"):
            lostLeadsData[kdate] += 1
        else:
            currentLeadsData[kdate] += 1

    for data in (billsData, lostLeadsData, wonLeadsData, currentLeadsData):
        kdates = data.keys()
        kdates.sort()
        isoKdates = [a.isoformat() for a in kdates]  # List of date as string in ISO format
        if len(kdates) > 0 and kdates[0] < minDate:
            minDate = kdates[0]
        data = zip(isoKdates, sortedValues(data))
        if not data:
            data = ((0, 0))
        graph_data.append(data)

    minDate = previousMonth(minDate)

    return render(request, "crm/graph_company_business_activity_jqp.html",
                  {"graph_data": json.dumps(graph_data),
                   "series_colors": COLORS,
                   "min_date": minDate.isoformat(),
                   "user": request.user})
