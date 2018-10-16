"""
Module for celery tasks.
"""
from collections import OrderedDict
from datetime import datetime
import json
import logging

from celery.schedules import crontab
from celery.task import periodic_task, task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import F
from django.db.models.expressions import RawSQL
from django.db.models.query_utils import Q
from django.http.response import Http404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from lms import CELERY_APP
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from rg_instructor_analytics.models import EnrollmentByStudent, EnrollmentTabCache, GradeStatistic, LastGradeStatUpdate
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

try:
    from lms.djangoapps.grades.new.course_grade_factory import CourseGradeFactory
except ImportError:
    try:
        from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
    except ImportError:
        # Hawthorn release:
        from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory


log = logging.getLogger(__name__)
DEFAULT_DATE_TIME = datetime(2000, 1, 1, 0, 0)


@CELERY_APP.task
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


cron_enroll_settings = getattr(
    settings, 'RG_ANALYTICS_ENROLLMENT_STAT_UPDATE',
    {
        'hour': '*/6',
    }
)


@periodic_task(run_every=crontab(**cron_enroll_settings))
def enrollment_collector_date():
    """
    Task for update enrollment statistic.
    """
    last_stat = EnrollmentByStudent.objects.all().order_by('-last_update')
    if last_stat.exists():
        last_update = last_stat.first().last_update
    else:
        last_update = DEFAULT_DATE_TIME
    enrollments_history = (
        CourseEnrollment.history
        .filter(~Q(history_type='+'))
        .filter(history_date__gt=last_update)
        .values("history_date", "is_active", "user", "course_id")
        .order_by('history_date')
    )
    users_state = {
        (enrol['student'], enrol['course_id']): {'last_update': enrol['last_update'], 'state': enrol['state']}
        for enrol in EnrollmentByStudent.objects.all().values("course_id", "student", "last_update", "state", )
    }

    result_stat = {}

    exist_stat = EnrollmentTabCache.objects.filter(
        created__exact=RawSQL(
            "(SELECT MAX(t2.created) FROM rg_instructor_analytics_enrollmenttabcache t2 " +
            "WHERE (t2.course_id = rg_instructor_analytics_enrollmenttabcache.course_id))", ())
    )

    total_stat = {}
    if exist_stat.exists():
        for stat in exist_stat:
            result_stat[stat.created, str(stat.course_id)] = {
                'unenroll': stat.unenroll,
                'enroll': stat.enroll,
                'total': stat.total,
            }
            total_stat[str(stat.course_id)] = stat.total

    for history_item in enrollments_history:
        key = history_item['user'], history_item['course_id']
        if key in users_state and users_state[key]['state'] == history_item['is_active']:
            continue
        users_state[key] = {
            'last_update': history_item['history_date'],
            'state': history_item['is_active'],
        }
        total_key = (history_item['history_date'].date(), history_item['course_id'])
        if total_key not in result_stat:
            result_stat[total_key] = {
                'unenroll': 0,
                'enroll': 0,
                'total': 0,
            }

        if history_item['course_id'] not in total_stat:
            total_stat[history_item['course_id']] = 0
        unenroll = 1 if history_item['is_active'] == 0 else 0
        enroll = 1 if history_item['is_active'] == 1 else 0
        total_stat[history_item['course_id']] += (enroll - unenroll)
        result_stat[total_key]['unenroll'] += unenroll
        result_stat[total_key]['enroll'] += enroll
        result_stat[total_key]['total'] = total_stat[history_item['course_id']]

    with transaction.atomic():
        for (user, course), value in users_state.iteritems():
            EnrollmentByStudent.objects.update_or_create(
                course_id=CourseKey.from_string(course), student=user,
                defaults={'last_update': value['last_update'], 'state': value['state']},
            )

        for (date, course), value in result_stat.iteritems():
            EnrollmentTabCache.objects.update_or_create(
                course_id=CourseKey.from_string(course), created=date,
                defaults={
                    'unenroll': value['unenroll'],
                    'enroll': value['enroll'],
                    'total': value['total'],
                },
            )


def get_items_for_grade_update():
    """
    Return an aggregate list of the users by the course, those grades need to be recalculated.
    """
    last_update_info = LastGradeStatUpdate.objects.all()
    # For first update we what get statistic for all enrollments,
    # otherwise - generate diff, based on the student activity.
    if last_update_info.exists():
        items_for_update = (
            StudentModule.objects
            .filter(module_type__exact='problem', modified__gt=last_update_info.last().last_update)
            .values('student__id', 'course_id')
            .order_by('student__id', 'course_id')
            .distinct()
        )
    else:
        items_for_update = (
            CourseEnrollment.objects
            .filter(is_active=True)
            .values('user__id', 'course_id')
            .order_by('user__id', 'course_id')
            .distinct()
            .annotate(student__id=F('user__id'))
            .values('student__id', 'course_id')
        )

    users_by_course = {}
    for item in items_for_update:
        if item['course_id'] not in users_by_course:
            users_by_course[item['course_id']] = []
        users_by_course[item['course_id']].append(item['student__id'])
    return users_by_course


def get_grade_summary(user_id, course):
    """
    Return the grade for the given student in the addressed course.
    """
    try:
        return CourseGradeFactory().create(User.objects.all().filter(id=user_id).first(), course).summary
    except PermissionDenied:
        return None


cron_grade_settings = getattr(
    settings, 'RG_ANALYTICS_GRADE_STAT_UPDATE',
    {
        'hour': '*/12',
    }
)


@periodic_task(run_every=crontab(**cron_grade_settings))
def grade_collector_stat():
    """
    Task for update user grades.
    """
    this_update_date = datetime.now()
    users_by_course = get_items_for_grade_update()

    collected_stat = []
    for course_string_id, users in users_by_course.iteritems():
        try:
            course_key = CourseKey.from_string(course_string_id)
            course = get_course_by_id(course_key, depth=0)
        except (InvalidKeyError, Http404):
            continue

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

    with transaction.atomic():
        for key_values, additional_info in collected_stat:
            key_values['defaults'] = additional_info
            GradeStatistic.objects.update_or_create(**key_values)

        LastGradeStatUpdate(last_update=this_update_date).save()


@task
def run_common_static_collection():
    """
    Task for updating analytics data.
    """
    grade_collector_stat()
    enrollment_collector_date()
