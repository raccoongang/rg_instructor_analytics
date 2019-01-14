"""
Models of the rg analytics.
"""

from django.contrib.auth.models import User
from django.db.models import (
    BooleanField, DateField, DateTimeField, FloatField, ForeignKey, IntegerField, Model, TextField
)

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class EnrollmentTabCache(Model):
    """
    Cache for the Enrollment tab.
    """

    course_id = CourseKeyField(max_length=255, db_index=True)
    created = DateField(db_index=True)
    unenroll = IntegerField(default=0)
    enroll = IntegerField(default=0)
    total = IntegerField(default=0)

    class Meta:
        """
        Meta class.
        """

        unique_together = ('course_id', 'created',)


class EnrollmentByStudent(Model):
    """
    Model for store last enrollment state of a user.
    """

    course_id = CourseKeyField(max_length=255, db_index=True)
    student = IntegerField(db_index=True)
    last_update = DateTimeField(db_index=True, blank=True, null=True)
    state = BooleanField()

    class Meta:
        """
        Meta class.
        """

        unique_together = ('course_id', 'student',)


class GradeStatistic(Model):
    """
    Model for store grades of the student for each course.
    """

    course_id = CourseKeyField(max_length=255, db_index=True)
    student = ForeignKey(User)
    exam_info = TextField()
    # Represent total grade in range from 0 to 1; [0; 1]
    total = FloatField()

    class Meta:
        """
        Meta class.
        """

        unique_together = ('course_id', 'student',)


# TODO replace this table with the Redis.
class LastGradeStatUpdate(Model):
    """
    For the calculation diffs for the update.
    """

    last_update = DateTimeField(db_index=True)
