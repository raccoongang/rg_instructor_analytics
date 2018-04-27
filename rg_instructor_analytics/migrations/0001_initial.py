# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import openedx.core.djangoapps.xmodule_django.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EnrollmentByStudent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('last_update', models.DateTimeField(db_index=True)),
                ('state', models.PositiveSmallIntegerField()),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EnrollmentTabCache',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('created', models.DateField(db_index=True)),
                ('unenroll', models.IntegerField(default=0)),
                ('enroll', models.IntegerField(default=0)),
                ('total', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='TotalEnrollmentByCourse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(unique=True, max_length=255, db_index=True)),
                ('total', models.IntegerField(default=0)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='enrollmenttabcache',
            unique_together=set([('course_id', 'created')]),
        ),
        migrations.AlterUniqueTogether(
            name='enrollmentbystudent',
            unique_together=set([('course_id', 'student')]),
        ),
    ]
