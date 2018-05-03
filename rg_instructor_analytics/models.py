"""
Models of the rg analytics.
"""

from django.db.models import BooleanField, DateField, DateTimeField, IntegerField, Model, TextField, ForeignKey

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField
from django.contrib.auth.models import User


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


class GradeStatistic(Model):
    """
    Model for store grades of the student for each course
    """

    course_id = CourseKeyField(max_length=255, db_index=True)
    student = ForeignKey(User, db_index=True)
    exam_info = TextField()
    total = IntegerField()

    class Meta:
        """
        Meta class.
        """

        unique_together = ('course_id', 'student',)


# TODO replace this table with redis.
class LastGradeStatUpdate(Model):
    """
    Used for calculate diffs for update.
    """

    last_update = DateTimeField(db_index=True)
