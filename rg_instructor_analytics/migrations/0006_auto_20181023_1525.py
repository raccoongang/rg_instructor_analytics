# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rg_instructor_analytics', '0005_auto_20181011_0843'),
    ]

    operations = [
        migrations.DeleteModel(
            name='EnrollmentByStudent',
        ),
        migrations.DeleteModel(
            name='EnrollmentTabCache',
        ),
    ]
