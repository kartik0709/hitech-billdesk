# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-15 16:33
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('index', '0009_auto_20171013_1811'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='saleprice',
            options={'ordering': ['pid']},
        ),
        migrations.AlterField(
            model_name='transaction',
            name='datetime',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 15, 16, 33, 12, 663428, tzinfo=utc)),
        ),
    ]