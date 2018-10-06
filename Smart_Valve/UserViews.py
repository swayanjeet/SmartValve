from django.views.generic import CreateView, ListView, UpdateView
from Smart_Valve.models import Organization
from django.shortcuts import render, redirect, HttpResponse, render_to_response
from django.contrib.auth import authenticate, login
from Smart_Valve.models import User
from django.template import Context, RequestContext
import boto3
import base64


class UserCreateView(CreateView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'organization', 'email_address', 'phone_number']
    template_name = 'Users/user_create.html'
    success_url = '/users/list/'

    def form_valid(self, form):
        model = form.save(commit=False)
        model.role = 'USER'
        return super(UserCreateView, self).form_valid(form)

    def get_form(self, form_class=None):
        form = super(UserCreateView, self).get_form(form_class)  # instantiate using parent
        if self.request.user.role=="ORG_ADMIN":
            form.fields['organization'].queryset = Organization.objects.filter(id=self.request.user.organization.pk)
        elif self.request.user.role=="SUPER_ADMIN":
            form.fields['organization'].queryset = Organization.objects.all()
        return form


class UserListView(ListView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'created_date', 'role', 'organization', 'email_address', 'phone_number'
              , 'is_active', 'account_activated']
    template_name = 'Users/user_list.html'

    def get_queryset(self):
        if self.request.user.role=="ORG_ADMIN":
            return User.objects.filter(organization=self.request.user.organization, role='USER')
        elif self.request.user.role=="SUPER_ADMIN":
            return User.objects.filter(role='USER')

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context["title"] = "User List"
        context["users"] = self.get_queryset()
        context["dashboard_header"] = "Showing all the Users"
        context["headers"] = [f.name.replace("_", " ")
                                   for f in User._meta.get_fields()
                                   if f.name.upper() not in ["PASSWORD", "LOGENTRY", "VALVE"]]
        return context
