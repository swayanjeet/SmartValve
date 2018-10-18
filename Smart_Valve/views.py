from django.views.generic import View
from django.shortcuts import render, redirect, HttpResponse, render_to_response
from django.contrib.auth import authenticate, login, logout
from django.template import Context, RequestContext
from Smart_Valve.models import Valve, Organization, User
from Smart_Valve.MqttClient import MqttClient
import boto3
import base64
from botocore.exceptions import ClientError
from datetime import datetime
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from Smart_Valve.CognitoConstants import *
import time


class LoginView(View):
    context_dict={"title": "Login Page", "message_visible_flag": "none"}

    def post(self, request):
        username = None
        try:
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request=request, username=username, password=password, update=False)
            if user is not None and user.account_activated:
                return render(request, "sms_mfa.html", {"title": "SMS Authentication"}, self.context_dict)
            elif not user.account_activated:
                return render(request, "update_temp_password.html", {"title": "Update Password"}, self.context_dict)
            else:
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "danger"
                self.context_dict["message"] = "Username and Password couldn't be authenticated !!"
                return render(request, "login_view.html", self.context_dict)
        except ClientError as error:
            print error
            if error.response['Error']['Code'] == 'NotAuthorizedException':
                print "Wrong Username Password"
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "danger"
                self.context_dict["message"] = "Username and Password are wrong"
                return render(request, "login_view.html", self.context_dict)
            elif error.response['Error']['Code'] == "UserNotFoundException":
                print "User is not found with username {0}".format(username)
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "danger"
                self.context_dict["message"] = "your username doesn't exist"
                return render(request, "login_view.html", self.context_dict)
            else:
                print "Unexpected error: %s" % error
                print "Wrong Username Password"
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "danger"
                self.context_dict["message"] = "Unexpected error occurred. Please login again"
                return render(request, "login_view.html", self.context_dict)

    def get(self, request):
        self.context_dict["message_visible_flag"] = "none"
        return render(request, 'login_view.html', self.context_dict)


class UpdateTemporaryPassword(View):
    context_dict = {}

    def post(self, request):
        try:
            new_password = request.POST["new_password"]
            new_password_once_more = request.POST["new_password_once_more"]
            username = request.session["username"]
            if new_password != new_password_once_more:
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "alert alert-danger"
                self.context_dict["message"] = "Both passwords should match"
                return render(request, "update_temp_password.html", self.context_dict)
            else:
                user = authenticate(request=request, username=username, password=new_password, update=True)
                if user is not None:
                    user.account_activated = True
                    user.save()
                    print "Modified account activated flag"
                    return render(request, "sms_mfa.html", {"title": "SMS Authentication"})
                else:
                    self.context_dict["message_visible_flag"] = "block"
                    self.context_dict["message_class"] = "alert alert-danger"
                    self.context_dict["message"] = "Password couldn't be updated !!"
                    return render(request, "update_temp_password.html", self.context_dict)
        except ClientError as error:
            if error.response['Error']['Code'] == 'InvalidPasswordException':
                print "Wrong Username Password"
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "alert alert-danger"
                self.context_dict["message"] = "Password should have atleast one uppercase, one number, one lowercase and one special character.(Minimum length - 8)"
                return render(request, "update_temp_password.html", self.context_dict)
            else:
                print "Unexpected error: %s" % error
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "alert alert-danger"
                self.context_dict["message"] = "Unexpected error occurred. Please login again"
                return redirect('/login/')

    def get(self, request):
        if "CognitoSession" not in self.request.session:
            redirect('/login/')


class AuthenticateView(View):
    resend_otp_count = 0
    context_dict = {"message_visible_flag":"none"}

    def post(self, request):
        try:
            if request.POST["action"]=="enter_otp":
                mfa = request.POST["mfa"]
                username = request.session["username"]
                session = request.session["CognitoSession"]
                print session
                user = authenticate(request=request, username=username, mfa=mfa, session=session)
                if user is not None:
                    login(request, user)
                    return redirect('dashboard')
            elif request.POST["action"]=="resend_otp":
                if self.resend_otp_count <= 2:
                    username = request.POST["username"]
                    session = request.session["CognitoSession"]
                    conext_dict = dict()
                    conext_dict["user"] = {"username": username, "session": session}
                    client = boto3.client(AWS_COGNITO_APP_NAME,
                                          region_name=AWS_REGION_NAME,
                                          aws_access_key_id=base64.b64decode(AWS_ACCESS_KEY_ID),
                                          aws_secret_access_key=base64.b64decode(AWS_SECRET_KEY)
                                          )
                    response = client.resend_confirmation_code(
                        ClientId=base64.b64decode(APP_CLIENT_ID),
                        Username=username
                        )
                    return render(request, "sms_mfa.html", conext_dict)
                else:
                    redirect('/login/')
        except ClientError as error:
            print error
            if error.response['Error']['Code'] == 'CodeMismatchException':
                print "Wrong Username Password"
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "danger"
                self.context_dict["message"] = "OTP entered is wrong. Please enter correct OTP"
                return render(request, "sms_mfa.html", self.context_dict)
            elif error.response['Error']['Code'] == 'ExpiredCodeException':
                print "Wrong Username Password"
                self.context_dict["message_visible_flag"] = "block"
                self.context_dict["message_class"] = "danger"
                self.context_dict["message"] = "OTP is expired. Please login again"
                return render(request, "login_view.html", self.context_dict)

            # return render(request, "dashboard.html", self.context_dict)

    def get(self, request):
        if "CognitoSession" not in self.request.session:
            redirect('/login/')
        else:
            return render(request, "sms_mfa.html")


class DashBoardView(View):
    context_dict = {'title': 'Dashboard'}
    login_required = True

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
            self.context_dict["org_count"] = orgs.count()
            self.context_dict["user_count"] = 0
            self.context_dict["valve_count"] = 0
            for org in orgs:
                org.user_count = User.objects.filter(organization=org).count()
                users = User.objects.filter(organization=org)
                self.context_dict["user_count"] += users.count()
                org.valve_count = Valve.objects.filter(users__in=users).distinct().count()
                self.context_dict["valve_count"] += org.valve_count
            self.context_dict["headers"] = [f.name.replace("_", " ")
                                            for f in Organization._meta.get_fields()
                                            if f.name.upper() not in ["USER"]]
            self.context_dict["headers"].append("USERS CREATED")
            self.context_dict["headers"].append("VALVES CREATED")
            self.context_dict["orgs"]=orgs
            self.context_dict["org_admin_count"] = User.objects.filter(role="ORG_ADMIN").count()

    def get(self, request):
        self.get_context_for_dashboard(request)
        return render(request, 'dashboard.html', self.context_dict)


class LogoutView(View):

    def get(self, request):
        logout(request)
        for key in ['username','CognitoSession', 'IdToken', 'RefreshToken', 'AccessToken']:
            if key in request.session:
                del request.session[key]
        return redirect('/login/')


class UpdateState(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(UpdateState, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        output_dict = {"status": "SUCCESS"}
        try:
            # value updation, state updation, web-sockets, multiple user updation, transition state
            valve_id = int(request.POST["valve_id"])
            valve_state = request.POST["state"].upper()
            print valve_state
            valve = Valve.objects.get(pk=valve_id)
            if valve.current_state != "OPENING" or valve.current_state != "CLOSING":
                if valve_state == "OPEN":
                    valve.current_state = "OPENING"
                elif valve_state == "CLOSE":
                    valve.current_state = "CLOSING"
                # valve.current_state = valve_state
                valve.status_last_updated_at = datetime.now()
                topic = valve.state_topic.replace("<IMEI>", valve.imei_number)
                mqtt_client = MqttClient()
                mqtt_client.main(topic, json.dumps({"state": valve_state}))
                valve.save()
                time.sleep(5)
                valve.current_state = valve_state
                valve.status_last_updated_at = datetime.now()
                valve.save()
                output_dict = {"status": "SUCCESS", "current_state": valve_state, "last_updated_timestamp": valve.status_last_updated_at.strftime('%Y-%m-%d %H:%M')}
                return HttpResponse(content_type="application/json", content=json.dumps(output_dict))
            else:
                raise ValueError("valve is currently {0}".format(valve.current_state))
        except Exception as error:
            output_dict = {"status": "FAILED"}
            return HttpResponse(content_type="application/json", content=json.dumps(output_dict))