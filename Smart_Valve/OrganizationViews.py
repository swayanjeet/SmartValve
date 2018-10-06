from django.views.generic import CreateView, ListView, UpdateView
from Smart_Valve.models import Organization
from django.shortcuts import render, redirect, HttpResponse, render_to_response
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.template import Context, RequestContext
import boto3
import base64


class OrganizationCreateView(CreateView):
    model = Organization
    fields = ['name']
    template_name = 'organization/organization_create.html'
    success_url = '/organization_list/'


class OrganizationListView(ListView):
    model = Organization
    fields = ['name', 'slug', 'id']
    template_name = 'organization/organization_list.html'

    def get_queryset(self):
        return Organization.objects.all()

    def get_context_data(self, **kwargs):
        context = super(OrganizationListView, self).get_context_data(**kwargs)
        context["title"] = "Organization List"
        context["orgs"] = self.get_queryset()
        context["dashboard_header"] = "Showing all the Organizations"
        context["headers"] = [f.name.replace("_", " ")
                                        for f in Organization._meta.get_fields()
                                        if f.name.upper() not in ["USER"]]
        return context


class OrganizationUpdateView(UpdateView):
    model = Organization
    fields = ['name']
    template_name = 'organization/organization_edit.html'
    success_url = '/organization_list/'