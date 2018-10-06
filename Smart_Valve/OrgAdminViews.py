from django.views.generic import CreateView, ListView, UpdateView
from Smart_Valve.models import Organization
from django.shortcuts import render, redirect, HttpResponse, render_to_response
from django.contrib.auth import authenticate, login
from Smart_Valve.models import User
from django.template import Context, RequestContext
import boto3
import base64


class OrgAdminCreateView(CreateView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'organization', 'email_address', 'phone_number']
    template_name = 'OrgAdmins/org_admin_create.html'
    success_url = '/org_admins/list/'

    def form_valid(self, form):
        model = form.save(commit=False)
        model.role = 'ORG_ADMIN'
        return super(OrgAdminCreateView, self).form_valid(form)


class OrgAdminListView(ListView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'created_date', 'role', 'organization', 'email_address',
              'phone_number'
        , 'is_active', 'account_activated']
    template_name = 'OrgAdmins/org_admin_list.html'

    def get_queryset(self):
        return User.objects.filter(role='ORG_ADMIN')

    def get_context_data(self, **kwargs):
        context = super(OrgAdminListView, self).get_context_data(**kwargs)
        context["title"] = "OrgAdmin List"
        context["org_admins"] = self.get_queryset()
        context["dashboard_header"] = "Showing all the Org Admins created"
        context["headers"] = [f.name.replace("_", " ")
                                   for f in User._meta.get_fields()
                                   if f.name.upper() not in ["PASSWORD", "LOGENTRY", "VALVE"]]
        return context