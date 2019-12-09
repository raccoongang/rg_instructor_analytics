"""
Module for celery tasks.
"""
import json
import logging
from collections import OrderedDict
from datetime import datetime

from celery.schedules import crontab
from celery.task import periodic_task, task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import F, Q
from django.http.response import Http404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from rg_instructor_analytics.models import GradeStatistic, LastGradeStatUpdate
from rg_instructor_analytics.utils import get_course_instructors_ids
from xmodule.modulestore.django import modulestore

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from student.models import CourseEnrollment

HAWTHORN = False

try:
    from lms.djangoapps.grades.new.course_grade_factory import CourseGradeFactory
except ImportError:
    try:
        from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
    except ImportError:
        # Hawthorn release:
        from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
        HAWTHORN = True

try:
    from openedx.core.release import RELEASE_LINE
except ImportError:
    RELEASE_LINE = 'ficus'

if RELEASE_LINE == 'hawthorn':
    from rg_instructor_analytics.utils import hawthorn_specific as specific
else:
    from rg_instructor_analytics.utils import ginkgo_ficus_specific as specific


log = logging.getLogger(__name__)
DEFAULT_DATE_TIME = datetime(2000, 1, 1, 0, 0)


@task
def send_email_to_cohort(subject, message, students):
    """
    Send email task.
    """
    context = {'subject': subject, 'body': message}
    html_content = render_to_string('rg_instructor_analytics/cohort_email_temolate.html', context)
    text_content = strip_tags(html_content)
    from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    msg = EmailMultiAlternatives(subject, text_content, from_address, students)
    msg.encoding = 'UTF-8'
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)


def get_items_for_grade_update():
    """
    Return an aggregate list of the users by the course, those grades need to be recalculated.
    """
    last_update_info = LastGradeStatUpdate.objects.last()
    # For first update we what get statistic for all enrollments,
    # otherwise - generate diff, based on the student activity.
    if last_update_info:
        force_update_students = list(last_update_info.force_update_students.all().values_list('id', flat=True))
        items_for_update = list(
            StudentModule.objects
            .filter(
                Q(module_type__exact='problem')
                & Q(modified__gt=last_update_info.last_update)
                | Q(student_id__in=force_update_students)
            )
            .values('student__id', 'course_id')
            .order_by('student__id', 'course_id')
            .distinct()
        )
        # Remove records for students who never enrolled
        for item in items_for_update:
            try:
                course_key = specific.get_course_key(item['course_id'])
            except InvalidKeyError:
                continue
            enrolled_by_course = CourseEnrollment.objects.filter(
                course_id=course_key
            ).values_list('user__id', flat=True)
            if item['student__id'] not in enrolled_by_course:
                items_for_update.remove(item)

        items_for_update += list(
            CourseEnrollment.objects
            .filter(created__gt=last_update_info.last_update)
            .values('user__id', 'course_id')
            .annotate(student__id=F('user__id'))
            .values('student__id', 'course_id')
            .distinct()
        )

    else:
        items_for_update = (
            CourseEnrollment.objects
            .values('user__id', 'course_id')
            .annotate(student__id=F('user__id'))
            .values('student__id', 'course_id')
            .distinct()
        )

    users_by_course = dict(
        (c, list())
        for c in CourseEnrollment.objects.all().values_list('course_id', flat=True).distinct()
    )
    [users_by_course[i['course_id']].append(i['student__id']) for i in items_for_update]
    return users_by_course


def get_grade_summary(user_id, course):
    """
    Return the grade for the given student in the addressed course.
    """
    try:
        if HAWTHORN:
            grade_summary = CourseGradeFactory().read(User.objects.all().filter(id=user_id).first(), course).summary
        else:
            grade_summary = CourseGradeFactory().create(User.objects.all().filter(id=user_id).first(), course).summary
        return grade_summary
    except PermissionDenied:
        return None


cron_grade_settings = getattr(
    settings, 'RG_ANALYTICS_GRADE_STAT_UPDATE',
    {
        'minute': str(settings.FEATURES.get('RG_ANALYTICS_GRADE_CRON_MINUTE', '0')),
        'hour': str(settings.FEATURES.get('RG_ANALYTICS_GRADE_CRON_HOUR', '*/6')),
        'day_of_month': str(settings.FEATURES.get('RG_ANALYTICS_GRADE_CRON_DOM', '*')),
        'day_of_week': str(settings.FEATURES.get('RG_ANALYTICS_GRADE_CRON_DOW', '*')),
        'month_of_year': str(settings.FEATURES.get('RG_ANALYTICS_GRADE_CRON_MONTH', '*')),
    }
)


@periodic_task(run_every=crontab(**cron_grade_settings))
def grade_collector_stat():
    """
    Task for update user grades.
    """
    this_update_date = datetime.now()
    logging.info('Task grade_collector_stat started at {}'.format(this_update_date))
    users_by_course = get_items_for_grade_update()
    collected_stat = []

    for course_string_id, users in users_by_course.iteritems():
        try:
            course_key = CourseKey.from_string(str(course_string_id))
            course = get_course_by_id(course_key, depth=0)
        except (InvalidKeyError, Http404):
            continue

        instructor_user_ids = get_course_instructors_ids(course_key)
        users = list(set(users) - set(instructor_user_ids))

        with modulestore().bulk_operations(course_key):
            for user in users:
                grades = get_grade_summary(user, course)
                if not grades:
                    continue
                exam_info = OrderedDict()
                for grade in grades['section_breakdown']:
                    exam_info[grade['label']] = int(grade['percent'] * 100.0)
                exam_info['total'] = int(grades['percent'] * 100.0)

                collected_stat.append(
                    (
                        {'course_id': course_key, 'student_id': user},
                        {'exam_info': json.dumps(exam_info), 'total': grades['percent']}
                    )
                )
        GradeStatistic.objects.filter(course_id=course_key, student_id__in=instructor_user_ids).delete()

    with transaction.atomic():
        for key_values, additional_info in collected_stat:
            key_values['defaults'] = additional_info
            GradeStatistic.objects.update_or_create(**key_values)

        lgsu = LastGradeStatUpdate(last_update=this_update_date)
        lgsu.save()
        # Leave 3 last records
        if lgsu.id > 3:
            LastGradeStatUpdate.objects.filter(id__lt=lgsu.id - 3).delete()


@task
def run_common_static_collection():
    """
    Task for updating analytics data.
    """
    grade_collector_stat()
