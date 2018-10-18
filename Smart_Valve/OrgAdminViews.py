from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from Smart_Valve.models import User
from botocore.exceptions import ClientError
from Smart_Valve.CognitoConstants import *
from django import forms
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
        context["headers"]+=["EDIT","DELETE"]
        return context


class OrgAdminEditView(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email_address', 'phone_number']
    template_name = 'OrgAdmins/org_admin_update.html'
    success_url = '/org_admins/list/'

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
        return super(OrgAdminEditView, self).form_valid(form)


class OrgAdminDeleteView(DeleteView):
    model = User
    template_name = 'OrgAdmins/org_admin_delete.html'
    success_url = '/org_admins/list'
