from django.views.generic import CreateView, ListView, UpdateView
from Smart_Valve.models import Valve, User
from django.shortcuts import render, redirect, HttpResponse, render_to_response
from django.contrib.auth import authenticate, login
from django.template import Context, RequestContext
import boto3
import base64


class ValveCreateView(CreateView):
    model = Valve
    fields = ['name','users','state_topic','status_topic','imei_number']
    template_name = 'Valves/valve_create.html'
    success_url = '/valves/list/'

    def get_form(self, form_class=None):
        form = super(ValveCreateView, self).get_form(form_class)  # instantiate using parent
        if self.request.user.role=="ORG_ADMIN":
            form.fields['users'].queryset = User.objects.filter(organization=self.request.user.organization, role='USER')
        elif self.request.user.role=="SUPER_ADMIN":
            form.fields['users'].queryset = User.objects.filter(role='USER')
        return form

class ValveListView(ListView):
    model = Valve
    fields = ['name', 'users', 'state_topic', 'status_topic','imei_number']
    template_name = 'Valves/valve_list.html'

    def get_queryset(self):
        valves = None
        if self.request.user.role=="USER":
            valves = Valve.objects.filter(users=self.request.user)
        elif self.request.user.role=="ORG_ADMIN":
            users = User.objects.filter(organization=self.request.user.organization, role="USER")
            valves = Valve.objects.filter(users__in=users.all()).distinct()
        elif self.request.user.role=="SUPER_ADMIN":
            users = User.objects.filter(role="USER")
            valves = Valve.objects.filter(users__in=users.all()).distinct()
        return valves

    def get_context_data(self, **kwargs):
        context = super(ValveListView, self).get_context_data(**kwargs)
        context["title"] = "Valves List"
        context["valves"] = self.get_queryset()
        context["dashboard_header"] = "Showing all the Valves"
        context["headers"] = [f.name.replace("_", " ")
                                        for f in Valve._meta.get_fields()
                                        if f.name.upper() not in ["STATE_TOPIC", "STATUS_TOPIC", "USERS"]]
        if self.request.user.role in ["ORG_ADMIN", "SUPER_ADMIN"]:
            context["inner_headers"] = ["username","first_name","last_name","organization"]
            context["inner_headers"] = [header.upper().replace("_"," ") for header in context["inner_headers"]]
        return context


class ValveEditView(UpdateView):
    model = Valve
    fields = ['name','users','state_topic','status_topic','imei_number']
    template_name = 'Valves/valve_update.html'
    success_url = '/valves/list/'

    def get_form(self, form_class=None):
        form = super(ValveEditView, self).get_form(form_class)  # instantiate using parent
        if self.request.user.role=="ORG_ADMIN":
            form.fields['users'].queryset = User.objects.filter(organization=self.request.user.organization, role='USER')
        elif self.request.user.role=="SUPER_ADMIN":
            form.fields['users'].queryset = User.objects.filter(role='USER')
        return form