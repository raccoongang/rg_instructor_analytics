# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import openedx.core.djangoapps.xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        ('rg_instructor_analytics', '0002_auto_20180426_1140'),
    ]

    operations = [
        migrations.CreateModel(
            name='TotalEnrollmentByCourse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(unique=True, max_length=255, db_index=True)),
                ('total', models.IntegerField(default=0)),
            ],
        ),
    ]
