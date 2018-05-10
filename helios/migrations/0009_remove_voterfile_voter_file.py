# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('helios', '0008_poll_forum_last_periodic_notification_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='voterfile',
            name='voter_file',
        ),
    ]
