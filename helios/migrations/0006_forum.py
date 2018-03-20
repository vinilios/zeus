# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import helios.models


class Migration(migrations.Migration):

    dependencies = [
        ('helios', '0005_election_cast_consent_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='forum_description',
            field=models.TextField(null=True, verbose_name='Forum description', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='poll',
            name='forum_enabled',
            field=models.BooleanField(default=False, verbose_name='Election forum enabled'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='poll',
            name='forum_ends_at',
            field=models.DateTimeField(default=None, help_text='Forum access ends at', null=True, verbose_name='Forum access ends at', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='poll',
            name='forum_extended_until',
            field=models.DateTimeField(default=None, help_text='Forum access ends at', null=True, verbose_name='Forum extension date', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='poll',
            name='forum_starts_at',
            field=models.DateTimeField(default=None, help_text='Forum access starts at', null=True, verbose_name='Forum access starts at', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='election',
            name='cast_consent_text',
            field=models.TextField(default=None, help_text='Require voters to accept specified terms in order to cast a vote.', null=True, verbose_name='Cast consent test', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pollmix',
            name='mix_file',
            field=models.FileField(default=None, storage=helios.models.CustomFileSystemStorage(), null=True, upload_to=helios.models.dummy_upload_to),
            preserve_default=True,
        ),
    ]
