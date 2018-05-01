"""
Models of the rg analytics.
"""

from django.contrib.auth.models import User
from django.db.models import BooleanField, DateField, DateTimeField, ForeignKey, IntegerField, Model, TextField

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
    student = IntegerField()
    last_update = DateTimeField(db_index=True)
    state = BooleanField()

    class Meta:
        """
        Meta class.
        """

        unique_together = ('course_id', 'student',)