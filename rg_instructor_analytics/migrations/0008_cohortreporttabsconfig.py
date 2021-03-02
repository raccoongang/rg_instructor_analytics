# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rg_instructor_analytics', '0007_instructortabsconfig'),
    ]

    operations = [
        migrations.CreateModel(
            name='CohortReportTabsConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enrollment_stats', models.BooleanField(default=False, verbose_name='Enrollment stats')),
                ('activities', models.BooleanField(default=False, verbose_name='Activities')),
                ('problems', models.BooleanField(default=False, verbose_name='Problems')),
                ('students_info', models.BooleanField(default=True, verbose_name="Students' Info")),
                ('clusters', models.BooleanField(default=False, verbose_name='Clusters')),
                ('progress_funnel', models.BooleanField(default=True, verbose_name='Progress Funnel')),
                ('suggestions', models.BooleanField(default=False, verbose_name='Suggestions')),
                ('user', models.OneToOneField(verbose_name='Instructor', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
