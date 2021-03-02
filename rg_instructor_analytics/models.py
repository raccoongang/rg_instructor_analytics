"""
Models of the rg analytics.
"""

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField
from student.models import CourseEnrollment


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

    @property
    def is_enrolled(self):
        """
        Return True if the user is enrolled in the course. Otherwise, returns False.
        """
        return CourseEnrollment.is_enrolled(self.student, self.course_id)


# TODO replace this table with the Redis.
class LastGradeStatUpdate(models.Model):
    """
    For the calculation diffs for the update.
    """

    last_update = models.DateTimeField(db_index=True)


class InstructorTabsConfig(models.Model):
    """
    Model for configuring instructor analytics tabs.
    """

    user = models.OneToOneField(User, verbose_name=_('Instructor'))
    enrollment_stats = models.BooleanField(default=True, verbose_name=_('Enrollment stats'))
    activities = models.BooleanField(default=True, verbose_name=_('Activities'))
    problems = models.BooleanField(default=True, verbose_name=_('Problems'))
    students_info = models.BooleanField(default=True, verbose_name=_('Students\' Info'))
    clusters = models.BooleanField(default=True, verbose_name=_('Clusters'))
    progress_funnel = models.BooleanField(default=True, verbose_name=_('Progress Funnel'))
    suggestions = models.BooleanField(default=True, verbose_name=_('Suggestions'))

    @classmethod
    def get_tabs_names(cls):
        """
        Return all tabs names.
        """
        return [f.name for f in cls._meta.get_fields() if f.name not in ('user', 'id')]

    @classmethod
    def tabs_for_user(cls, user):
        """
        Return enabled tabs names.
        """
        fields = cls.get_tabs_names()
        try:
            conf = cls.objects.get(user=user).__dict__
        except cls.DoesNotExist:
            return fields
        else:
            return [k for k, v in conf.items() if k in fields and v]

    def __unicode__(self):
        """
        Return human readable object name.
        """
        return "Tabs config for user: {}".format(self.user)


class CohortReportTabsConfig(models.Model):
    """
    Model for configuring cohort report tabs.
    """

    user = models.OneToOneField(User, verbose_name=_('Cohort Leader'))
    enrollment_stats = models.BooleanField(default=False, verbose_name=_('Enrollment stats'))
    activities = models.BooleanField(default=False, verbose_name=_('Activities'))
    problems = models.BooleanField(default=False, verbose_name=_('Problems'))
    students_info = models.BooleanField(default=True, verbose_name=_('Students\' Info'))
    clusters = models.BooleanField(default=False, verbose_name=_('Clusters'))
    progress_funnel = models.BooleanField(default=True, verbose_name=_('Progress Funnel'))
    suggestions = models.BooleanField(default=False, verbose_name=_('Suggestions'))

    @classmethod
    def get_tabs_names(cls):
        """
        Return all tabs names.
        """
        return [f.name for f in cls._meta.get_fields() if f.name not in ('user', 'id')]

    @classmethod
    def tabs_for_user(cls, user):
        """
        Return enabled tabs names.
        """
        fields = cls.get_tabs_names()
        try:
            conf = cls.objects.get(user=user).__dict__
        except cls.DoesNotExist:
            return fields
        else:
            return [k for k, v in conf.items() if k in fields and v]

    def __unicode__(self):
        """
        Return human readable object name.
        """
        return "Tabs config for user: {}".format(self.user)
