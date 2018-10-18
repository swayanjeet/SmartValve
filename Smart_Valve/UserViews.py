from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from Smart_Valve.models import Organization
from django.shortcuts import render, redirect, HttpResponse, render_to_response
from django.contrib.auth import authenticate, login
from Smart_Valve.models import User
from django.template import Context, RequestContext
from botocore.exceptions import ClientError
from django import forms
from Smart_Valve.CognitoConstants import *
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
        context["headers"] += ["EDIT", "DELETE"]
        return context


class UserEditView(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email_address', 'phone_number']
    template_name = 'Users/user_update.html'
    success_url = '/users/list/'

    def form_valid(self, form):
        try:
            model = form.save(commit=False)
            print model.username
            client = boto3.client(AWS_COGNITO_APP_NAME,
                                  region_name=AWS_REGION_NAME,
                                  aws_access_key_id=base64.b64decode(AWS_ACCESS_KEY_ID),
                                  aws_secret_access_key=base64.b64decode(AWS_SECRET_KEY)
                                  )
            response = client.admin_update_user_attributes(
                UserPoolId=AWS_USER_POOL_ID,
                Username=model.username,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': model.email_address
                    },
                    {
                        'Name': 'phone_number',
                        'Value': "+91" + str(model.phone_number)
                    },
                    {
                        'Name': 'custom:user_type',
                        'Value': model.role
                    },
                    {
                        'Name': 'custom:organization',
                        'Value': model.organization.name
                    }
                ]
            )

        except ClientError as error:
            print error
            if error.response['Error']['Code'] == 'UserNotFoundException':
                print "Wrong Username Password"
                raise forms.ValidationError("User doesn't exist")
        return super(UserEditView, self).form_valid(form)


class UserDeleteView(DeleteView):
    model = User
    template_name = 'Users/user_delete.html'
    success_url = '/users/list'
    fields = ['first_name', 'last_name', 'email_address', 'phone_number']
