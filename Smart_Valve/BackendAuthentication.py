from Smart_Valve.models import User
from Smart_Valve.CognitoConstants import *
import base64
import boto3



class SmsMfaAuth:
    def authenticate(self, request, username=None, mfa=None, session=None):
        client = boto3.client(AWS_COGNITO_APP_NAME,
                              region_name=AWS_REGION_NAME,
                              aws_access_key_id=base64.b64decode(AWS_ACCESS_KEY_ID),
                              aws_secret_access_key=base64.b64decode(AWS_SECRET_KEY)
                              )
        response = client.respond_to_auth_challenge(
            ClientId=base64.b64decode(APP_CLIENT_ID),
            ChallengeName='SMS_MFA',
            Session=session,
            ChallengeResponses={
                "USERNAME": username,
                "SMS_MFA_CODE": mfa
            })
        print response
        try:
            if "AuthenticationResult" in response:
                user = User.objects.get(username=username)
                request.session["RefreshToken"] = response["AuthenticationResult"]["RefreshToken"]
                request.session["IdToken"] = response["AuthenticationResult"]["IdToken"]
                request.session["AccessToken"] = response["AuthenticationResult"]["AccessToken"]
                request.session["username"] = username
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None




class AuthenticationUserNamePassword:

    def authenticate(self, request, username=None, password=None, update=False):
        client = boto3.client(AWS_COGNITO_APP_NAME,
                              region_name=AWS_REGION_NAME,
                              aws_access_key_id=base64.b64decode(AWS_ACCESS_KEY_ID),
                              aws_secret_access_key=base64.b64decode(AWS_SECRET_KEY)
                              )
        if not update:
            response = client.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    "USERNAME": username,
                    "PASSWORD": password
                },
                ClientId=base64.b64decode(APP_CLIENT_ID),
            )
            print response
            try:
                if "Session" in response:
                    user = User.objects.get(username=username)
                    request.session["CognitoSession"] = response["Session"]
                    request.session["username"] = username
                    return user
            except User.DoesNotExist:
                return None
        elif update:
            print request.session["CognitoSession"]
            response = client.respond_to_auth_challenge(
                ClientId=base64.b64decode(APP_CLIENT_ID),
                ChallengeName='NEW_PASSWORD_REQUIRED',
                Session=request.session["CognitoSession"],
                ChallengeResponses={
                    "USERNAME": username,
                    "NEW_PASSWORD": password
                })
            print response
            try:
                if "Session" in response:
                    user = User.objects.get(username=username)
                    request.session["CognitoSession"] = response["Session"]
                    request.session["username"] = username
                    return user
            except User.DoesNotExist:
                return None

