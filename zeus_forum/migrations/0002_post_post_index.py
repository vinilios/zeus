# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zeus_forum', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='post_index',
            field=models.PositiveIntegerField(default=None, null=True),
            preserve_default=True,
        ),
    ]
