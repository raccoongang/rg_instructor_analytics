# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rg_instructor_analytics', '0003_auto_20180503_1149'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gradestatistic',
            name='total',
            field=models.FloatField(),
        ),
    ]
