from __future__ import unicode_literals

from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.utils.text import slugify
from datetime import datetime
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _
import base64
import boto3
from botocore.exceptions import ClientError

AWS_COGNITO_APP_NAME = 'cognito-idp'
AWS_USER_POOL_ID = 'us-east-2_CEuXbG7OK'
AWS_REGION_NAME = "us-east-2"
AWS_ACCESS_KEY_ID = "QUtJQUpJM080VlNKV1o3TVI1WEE="
AWS_SECRET_KEY = "eHA1OXFkTnM2QThEay9HQzNmbUhGbnJVSXFERVE0Z2NPNHo2NTJkQw=="
VALUE_TOPIC_SUFFIX = "_value"
STATE_TOPIC_SUFFIX = "_state"


class Organization(models.Model):
    name = models.CharField(max_length=100)
    slug = models.CharField(max_length=50)
    id = models.AutoField(primary_key=True)

    class Meta:
        permissions = (
            ("CREATE_ORGANIZATION", "Has the ability to create organizations"),
            ("EDIT_ORGANIZATION", "Has the ability to edit organization")
        )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(Organization, self).save(*args, **kwargs)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, **extra_fields):
        if not username:
            raise ValueError('The given username must be set')
        organization_id = extra_fields["organization_id"]
        organization = Organization.objects.get(pk=organization_id)
        client = boto3.client(AWS_COGNITO_APP_NAME,
                              region_name=AWS_REGION_NAME,
                              aws_access_key_id=base64.b64decode(AWS_ACCESS_KEY_ID),
                              aws_secret_access_key=base64.b64decode(AWS_SECRET_KEY)
                              )
        try:
            response = client.admin_create_user(
                UserPoolId=AWS_USER_POOL_ID,
                Username=username,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': extra_fields["email_address"]
                    },
                    {
                        'Name': 'phone_number',
                        'Value': "+91" + str(extra_fields["phone_number"])
                    },
                    {
                        'Name': 'custom:user_type',
                        'Value': extra_fields["role"]
                    },
                    {
                        'Name': 'custom:organization',
                        'Value': organization.name
                    }
                ],
                ForceAliasCreation=False,
                DesiredDeliveryMediums=["EMAIL", "SMS"]
            )
            print "Cognito User Created"
        except ClientError as error:
            if error.response['Error']['Code'] == 'UsernameExistsException':
                print("Username already exists")
                raise error
            else:
                print("Other Error")
                raise error
        user = self.model(username=username, **extra_fields)
        user.save(using=self._db)
        return user

    def create_user(self, username, **extra_fields):
        return self._create_user(username, role='USER', **extra_fields)

    def create_org_admin(self, username, **extra_fields):
        return self._create_user(username, role='ORG_ADMIN', **extra_fields)

    def create_superuser(self, username, **extra_fields):
        return self._create_user(username, role='SUPER_ADMIN', **extra_fields)


class User(AbstractBaseUser):
    username = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    created_date = models.DateTimeField(default=datetime.now())
    role = models.CharField(max_length=100, default="USER")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True)
    email_address = models.EmailField()
    phone_number = models.BigIntegerField(null=True)
    is_active = models.BooleanField(_('active'), default=True)
    account_activated = models.BooleanField(_('activated'), default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['role', 'organization', 'phone_number']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        permissions = (
            ("CREATE_USER", "Has the ability to create USERS"),
            ("CREATE_ORG_ADMINS", "Has the ability to create ORG_ADMINS")
        )

    def __str__(self):
        return self.username

    def get_full_name(self):
        '''
        Returns the first_name plus the last_name, with a space in between.
        '''
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        '''
        Returns the short name for the user.
        '''
        return self.first_name

    def save(self, *args, **kwargs):
        if not self.pk:
            client = boto3.client(AWS_COGNITO_APP_NAME,
                                  region_name=AWS_REGION_NAME,
                                  aws_access_key_id=base64.b64decode(AWS_ACCESS_KEY_ID),
                                  aws_secret_access_key=base64.b64decode(AWS_SECRET_KEY)
                                  )
            try:
                response = client.admin_create_user(
                    UserPoolId=AWS_USER_POOL_ID,
                    Username=self.username,
                    UserAttributes=[
                        {
                            'Name': 'email',
                            'Value': self.email_address
                        },
                        {
                            'Name': 'phone_number',
                            'Value': "+91" + str(self.phone_number)
                        },
                        {
                            'Name': 'custom:user_type',
                            'Value': self.role
                        },
                        {
                            'Name': 'custom:organization',
                            'Value': self.organization.name
                        }
                    ],
                    ForceAliasCreation=False,
                    DesiredDeliveryMediums=["EMAIL", "SMS"]
                )
                print "Cognito User Created"
            except ClientError as error:
                if error.response['Error']['Code'] == 'UsernameExistsException':
                    print("Username already exists")
                    raise error
                else:
                    print("Other Error")
                    raise error
            super(User, self).save(*args, **kwargs)


class Valve(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(User)
    state_topic = models.CharField(max_length=100, null=True)
    status_topic = models.CharField(max_length=100, null=True)
    imei_number = models.CharField(max_length=500)
    current_state = models.CharField(max_length=100, default='UNKNOWN')
    current_status = models.CharField(max_length=100, default='UNKNOWN')
    status_last_updated_at = models.TimeField(default=datetime.now())
