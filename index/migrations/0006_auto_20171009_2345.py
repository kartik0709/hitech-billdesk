# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-09 18:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('index', '0005_auto_20171009_2312'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='saleprice',
            name='id',
        ),
        migrations.AlterField(
            model_name='saleprice',
            name='pid',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='index.Purchase'),
        ),
    ]
