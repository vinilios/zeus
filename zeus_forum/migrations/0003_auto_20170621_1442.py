# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zeus_forum', '0002_post_post_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='is_replaced',
            field=models.BooleanField(default=False, db_index=True),
            preserve_default=True,
        ),
    ]
