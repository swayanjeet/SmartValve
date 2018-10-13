from django.conf import Settings
from Smart_Valve.models import User
import base64
import boto3

AWS_COGNITO_APP_NAME = 'cognito-idp'
AWS_USER_POOL_ID = 'us-east-2_5NYzGJJKB'
AWS_REGION_NAME = "us-east-2"
AWS_ACCESS_KEY_ID = "QUtJQUpJM080VlNKV1o3TVI1WEE="
AWS_SECRET_KEY = "eHA1OXFkTnM2QThEay9HQzNmbUhGbnJVSXFERVE0Z2NPNHo2NTJkQw=="
APP_CLIENT_ID = "NHQyb25ibGdiMDN2ZmFlZmJ1ZzR2MzI4bg=="


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
                    user.session = response["Session"]
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
                    return user
            except User.DoesNotExist:
                return None

