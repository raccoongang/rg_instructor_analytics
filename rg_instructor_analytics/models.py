from django.db.models import Model, DateTimeField, IntegerField, ForeignKey, PositiveSmallIntegerField, DateField
from django.contrib.auth.models import User
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class EnrollmentTabCache(Model):
    course_id = CourseKeyField(max_length=255, db_index=True)
    created = DateField(auto_now_add=False, db_index=True)
    unenroll = IntegerField(default=0)
    enroll = IntegerField(default=0)
    total = IntegerField(default=0)

    class Meta:
        unique_together = ('course_id', 'created',)


class EnrollmentByStudent(Model):
    course_id = CourseKeyField(max_length=255, db_index=True)
    student = ForeignKey(User, db_index=True)
    last_update = DateTimeField(auto_now_add=False, db_index=True)
    state = PositiveSmallIntegerField()

    class Meta:
        unique_together = ('course_id', 'student',)


class TotalEnrollmentByCourse(Model):
    course_id = CourseKeyField(max_length=255, db_index=True,unique=True)
    total = IntegerField(default=0)
