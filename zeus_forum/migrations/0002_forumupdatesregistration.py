# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('helios', '0008_poll_forum_last_periodic_notification_at'),
        ('zeus_forum', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForumUpdatesRegistration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('frequency', models.CharField(max_length=100, choices=[(b'periodic', 'Daily'), (b'instant', 'Instant')])),
                ('active', models.BooleanField(default=True)),
                ('last_notified_at', models.DateTimeField(default=None, auto_now=True, null=True)),
                ('poll', models.ForeignKey(default=None, blank=True, to='helios.Poll', null=True)),
                ('voter', models.ForeignKey(default=None, to='helios.Voter', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
