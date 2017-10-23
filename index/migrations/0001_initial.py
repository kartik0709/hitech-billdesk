# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-09 07:27
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pid', models.CharField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('quantity', models.IntegerField()),
                ('vendor', models.CharField(max_length=500)),
                ('purchase_price', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('percent_gst', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('percent_cgst', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('purchase_cgst', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('percent_sgst', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('purchase_sgst', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('percent_igst', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('purchase_igst', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('total_purchase_tax', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('purchase_total', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
            ],
            options={
                'ordering': ['pid'],
            },
        ),
        migrations.CreateModel(
            name='PurchaseHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pid', models.CharField(max_length=100)),
                ('quantity', models.IntegerField()),
                ('pprice', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('ptax', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0)])),
                ('datetime', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['-datetime'],
            },
        ),
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('quantity', models.IntegerField()),
                ('sale_price', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('sale_cgst', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('sale_sgst', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('sale_igst', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('sale_total', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('pid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='index.Purchase')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=50, unique=True, validators=[django.core.validators.MinLengthValidator(5, message='Username cannot be less than 5 characters')])),
                ('hash', models.TextField()),
                ('name', models.CharField(max_length=50)),
                ('purchase_total', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0)])),
                ('sale_total', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0)])),
            ],
            options={
                'ordering': ['username'],
            },
        ),
    ]
