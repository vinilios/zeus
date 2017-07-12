# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import helios.models


class Migration(migrations.Migration):

    dependencies = [
        ('helios', '0002_forum'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pollmix',
            name='mix_file',
            field=models.FileField(default=None, storage=helios.models.CustomFileSystemStorage(), null=True, upload_to=helios.models.dummy_upload_to),
            preserve_default=True,
        ),
    ]
