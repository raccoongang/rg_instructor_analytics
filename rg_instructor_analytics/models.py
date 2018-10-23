"""
Models of the rg analytics.
"""

from django.contrib.auth.models import User
from django.db import models

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class GradeStatistic(models.Model):
    """
    Model for store grades of the student for each course.
    """

    course_id = CourseKeyField(max_length=255, db_index=True)
    student = models.ForeignKey(User)
    exam_info = models.TextField()
    # Represent total grade in range from 0 to 1; [0; 1]
    total = models.FloatField()

    class Meta:
        """
        Meta class.
        """

        unique_together = ('course_id', 'student',)


# TODO replace this table with the Redis.
class LastGradeStatUpdate(models.Model):
    """
    For the calculation diffs for the update.
    """

    last_update = models.DateTimeField(db_index=True)
