# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def rename_stv(apps, schema_editor):
    Election = apps.get_model('helios', 'Election')
    Poll = apps.get_model('helios', 'Poll')
    Poll.objects.filter(election__election_module='stv').update(stv_droop=False)
    Election.objects.filter(election_module='stv').update(
        election_module='unicouncilsgr')


def revert_stv(apps, schema_editor):
    Election = apps.get_model('helios', 'Election')
    Poll = apps.get_model('helios', 'Poll')
    Election.objects.filter(election_module='unicouncilsgr').update(
        election_module='stv')


class Migration(migrations.Migration):

    dependencies = [
        ('helios', '0010_stv'),
    ]

    operations = [
        migrations.RunPython(rename_stv, revert_stv)
    ]
