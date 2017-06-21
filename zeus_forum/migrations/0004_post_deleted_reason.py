# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zeus_forum', '0003_auto_20170621_1442'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='deleted_reason',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
