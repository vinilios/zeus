# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('helios', '0009_remove_voterfile_voter_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='stv_droop',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='election',
            name='election_module',
            field=models.CharField(default=b'simple', help_text='Choose the type of the election', max_length=250, verbose_name='Election type', choices=[(b'simple', 'Simple election with one or more questions'), (b'parties', 'Party lists election'), (b'score', 'Score voting election'), (b'unicouncilsgr', 'Greek Universities Governing Councils election'), (b'unigovgr', 'Greek Universities single governing bodies election'), (b'preference', 'Preferential voting'), (b'stv', 'Single transferable vote election')]),
            preserve_default=True,
        ),
    ]
