# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rg_instructor_analytics', '0004_auto_20180504_0746'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enrollmentbystudent',
            name='last_update',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='enrollmentbystudent',
            name='student',
            field=models.IntegerField(db_index=True),
        ),
    ]
