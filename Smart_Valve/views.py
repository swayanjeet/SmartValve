from django.views.generic import View
from django.shortcuts import render, redirect, HttpResponse, render_to_response
from django.contrib.auth import authenticate, login, logout
from django.template import Context, RequestContext
from Smart_Valve.models import Valve, Organization, User
import boto3
import base64
from botocore.exceptions import ClientError


AWS_COGNITO_APP_NAME = 'cognito-idp'
AWS_USER_POOL_ID = 'us-east-2_5NYzGJJKB'
AWS_REGION_NAME = "us-east-2"
AWS_ACCESS_KEY_ID = "QUtJQUpJM080VlNKV1o3TVI1WEE="
AWS_SECRET_KEY = "eHA1OXFkTnM2QThEay9HQzNmbUhGbnJVSXFERVE0Z2NPNHo2NTJkQw=="
APP_CLIENT_ID = "NHQyb25ibGdiMDN2ZmFlZmJ1ZzR2MzI4bg=="

class LoginView(View):
    context_dict={"title": "Login Page", "message_visible_flag": "none"}

    def post(self, request):
        try:
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request=request, username=username, password=password)
            if user is not None:
                return render(request, "sms_mfa.html", {"title": "SMS Authentication", "user": user})
            else:
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "alert alert-danger"
                self.context_dict["message"] = "Username and Password couldn't be authenticated !!"
                return render(request, "login_view.html", self.context_dict)
        except ClientError as error:
            if error.response['Error']['Code'] == 'NotAuthorizedException':
                print "Wrong Username Password"
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "alert alert-danger"
                self.context_dict["message"] = "Username and Password are wrong"
                return render(request, "login_view.html", self.context_dict)
            else:
                print "Unexpected error: %s" % error
                print "Wrong Username Password"
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "alert alert-danger"
                self.context_dict["message"] = "Unexpected error occurred. Please login again"
                return render(request, "login_view.html", self.context_dict)

    def get(self, request):
        return render(request, 'login_view.html')


class AuthenticateView(View):
    context_dict = {}

    def post(self, request):
        mfa = request.POST["mfa"]
        username = request.POST["username"]
        session = request.POST["session"]
        user = authenticate(request=request, username=username, mfa=mfa, session=session)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
            # return render(request, "dashboard.html", self.context_dict)

    def get(self, request):
        # if User.is_authenticated():
        #     return render()
        return render(request, "sms_mfa.html")


class DashBoardView(View):
    context_dict = {'title': 'Dashboard'}

    def get_context_for_dashboard(self, request):
        if request.user.role == "USER":
            valves = Valve.objects.filter(users=request.user)
            if valves.count() != 0:
                self.context_dict["dashboard_header"] = "Showing all the Valves"
                self.context_dict["valves"] = valves
                self.context_dict["headers"] = [f.name.replace("_", " ")
                                                for f in Valve._meta.get_fields()
                                                if f.name.upper() not in ["STATE_TOPIC", "STATUS_TOPIC", "USERS"]]
        elif request.user.role == "ORG_ADMIN":
            users = User.objects.filter(organization=request.user.organization, role="USER")
            for user in users:
                user.valve_count = Valve.objects.filter(users=user).count()
            if users.count() != 0:
                self.context_dict["users"] = users
                self.context_dict["headers"] = [f.name.replace("_", " ")
                                                for f in User._meta.get_fields()
                                                if f.name.upper() not in ["PASSWORD", "LOGENTRY", "VALVE"]]
                self.context_dict["headers"].append("VALVE COUNT")
                self.context_dict["dashboard_header"] = "Showing all the Users and Valves configured"
        elif request.user.role == "SUPER_ADMIN":
            self.context_dict["dashboard_header"] = "Showing all the Users and Valves configured"
            orgs = Organization.objects.all()
            for org in orgs:
                org.user_count = User.objects.filter(organization=org).count()
                users = User.objects.filter(organization=org)
                org.valve_count = Valve.objects.filter(users__in=users).distinct().count()
            self.context_dict["headers"] = [f.name.replace("_", " ")
                                            for f in Organization._meta.get_fields()
                                            if f.name.upper() not in ["USER"]]
            self.context_dict["headers"].append("USERS CREATED")
            self.context_dict["headers"].append("VALVES CREATED")
            self.context_dict["orgs"]=orgs

    def get(self, request):
        self.get_context_for_dashboard(request)
        return render(request, 'dashboard.html', self.context_dict)


class LogoutView(View):

    def get(self, request):
        logout(request)
        return redirect('/login/')