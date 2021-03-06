# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-10-06 12:10
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Smart_Valve', '0003_auto_20181002_1450'),
    ]

    operations = [
        migrations.CreateModel(
            name='Valve',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('state_topic', models.CharField(max_length=100, null=True)),
                ('status_topic', models.CharField(max_length=100, null=True)),
                ('imei_number', models.CharField(max_length=500)),
                ('current_state', models.CharField(default='UNKNOWN', max_length=100)),
                ('current_status', models.CharField(default='UNKNOWN', max_length=100)),
                ('status_last_updated_at', models.TimeField()),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime(2018, 10, 6, 17, 40, 55, 465000)),
        ),
        migrations.AddField(
            model_name='valve',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]
