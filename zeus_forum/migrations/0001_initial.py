# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('helios', '0002_forum'),
        ('heliosauth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('posted_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(default=None, auto_now=True, null=True)),
                ('deleted_at', models.DateTimeField(default=None, null=True)),
                ('is_modification', models.BooleanField(default=False)),
                ('is_replaced', models.BooleanField(default=False, db_index=True)),
                ('title', models.CharField(default=None, max_length=300, null=True)),
                ('body', models.TextField()),
                ('user_type', models.CharField(max_length=100, choices=[(b'admin', b'Admin'), (b'voter', b'Voter')])),
                ('deleted', models.BooleanField(default=False, db_index=True)),
                ('deleted_reason', models.TextField(null=True, blank=True)),
                ('post_index', models.PositiveIntegerField(default=None, null=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('admin', models.ForeignKey(default=None, to='heliosauth.User', null=True)),
                ('deleted_by_admin', models.ForeignKey(related_name='deleted_posts', default=None, to='heliosauth.User', null=True)),
                ('election', models.ForeignKey(to='helios.Election')),
                ('parent', mptt.fields.TreeForeignKey(related_name='comments', blank=True, to='zeus_forum.Post', null=True)),
                ('poll', models.ForeignKey(default=None, blank=True, to='helios.Poll', null=True)),
                ('replaces', models.ForeignKey(related_name='replaced_by', default=None, to='zeus_forum.Post', null=True)),
                ('voter', models.ForeignKey(default=None, to='helios.Voter', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
