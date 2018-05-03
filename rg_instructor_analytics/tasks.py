"""
Module for celery tasks.
"""
import json
import logging
from collections import OrderedDict
from datetime import datetime, timedelta

from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import F
from django.db.models.query_utils import Q
from django.http.response import Http404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from lms import CELERY_APP
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from xmodule.modulestore.django import modulestore

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from rg_instructor_analytics.models import EnrollmentByStudent, EnrollmentTabCache, LastGradeStatUpdate, GradeStatistic
from student.models import CourseEnrollment

try:
    from lms.djangoapps.grades.new.course_grade_factory import CourseGradeFactory
except Exception:
    from lms.djangoapps.grades.new.course_grade import CourseGradeFactory


log = logging.getLogger(__name__)
ENROLLMENT_STAT_CACHE_BY_COURSE_KEY = 'ENROLLLMENT_STAT_CACHE_BY_COURSE_KEY'
GRADE_STAT_CACHE_BY_COURSE_KEY = 'GRADE_STAT_CACHE_BY_COURSE_KEY'
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


cron_settings = getattr(
    settings, 'RG_ANALYTICS_ENROLLMENT_STAT_UPDATE',
    {
        'hour': '*/6',
    }
)


@periodic_task(run_every=crontab(**cron_settings))
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

    total_stat = cache.get(ENROLLMENT_STAT_CACHE_BY_COURSE_KEY, {})
    result_stat = {}
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
            last_enrol = EnrollmentTabCache.objects.filter(course_id=CourseKey.from_string(history_item['course_id']))
            if not last_enrol.exists():
                total_stat[history_item['course_id']] = 0
            else:
                total_stat[history_item['course_id']] = last_enrol.last().total
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

    cache.set(ENROLLMENT_STAT_CACHE_BY_COURSE_KEY, total_stat)


def get_items_for_grade_update():
    last_update_info = LastGradeStatUpdate.objects.all()
    if last_update_info.exists():
        item_for_update = (
            StudentModule.objects
            .filter(module_type__exact='problem', modified__gt=last_update_info.last()['last_update'])
            .values('student__id', 'course_id')
            .order_by('student__id', 'course_id')
            .distinct()
        )
    else:
        item_for_update = (
            CourseEnrollment.objects
                .filter(is_active=True)
                .values('user__id', 'course_id')
                .order_by('user__id', 'course_id')
                .distinct()
                .annotate(student__id=F('user__id'))
                .values('student__id', 'course_id')
        )
        log.error(item_for_update)

    users_by_course = {}
    for item in item_for_update:
        if item['course_id'] not in users_by_course:
            users_by_course[item['course_id']] = []
        users_by_course[item['course_id']].append(item['student__id'])
    return users_by_course


def get_grade_summary(user_id, course):
    return CourseGradeFactory().create(User.objects.all().filter(id=user_id).first(), course).summary


# @periodic_task(run_every=crontab(**cron_settings))
@periodic_task(run_every=timedelta(seconds=10))
def grade_collector_stat():
    this_update_date = datetime.now()
    users_by_course = get_items_for_grade_update()
    log.error(users_by_course)

    collected_stat = []
    for course_string_id, users in users_by_course.iteritems():
        try:
            course_key = CourseKey.from_string(course_string_id)
            course = get_course_by_id(course_key, depth=0)
        except (InvalidKeyError,Http404):
            continue

        with modulestore().bulk_operations(course_key):
            for user in users:
                grades = get_grade_summary(user, course)
                exam_info = OrderedDict()
                for grade in grades['section_breakdown']:
                    exam_info[grade['label']] = int(grade['percent'] * 100.0)
                total = int(grades['percent'] * 100.0)
                exam_info['total'] = total

                collected_stat.append(
                    (
                        {'course_id': course_key, 'student_id': user},
                        {'exam_info': json.dumps(exam_info), 'total': int(grades['percent'] * 100.0)}
                    )
                )

    with transaction.atomic():
        for key_values, additiona_info in collected_stat:
            key_values['defaults'] = additiona_info
            log.error(key_values)
            GradeStatistic.objects.update_or_create(**key_values)

        LastGradeStatUpdate(last_update=this_update_date).save()
