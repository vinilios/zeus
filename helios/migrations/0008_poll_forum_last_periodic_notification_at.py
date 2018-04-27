# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('helios', '0007_new_election_module'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='forum_last_periodic_notification_at',
            field=models.DateTimeField(default=None, null=True),
            preserve_default=True,
        ),
    ]
