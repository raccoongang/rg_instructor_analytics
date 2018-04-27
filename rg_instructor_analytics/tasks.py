"""
Module for celery tasks.
"""
import json
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Max
from django.db.models.query_utils import Q
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from lms import CELERY_APP
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from datetime import timedelta, datetime

from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings

from rg_instructor_analytics.models import EnrollmentByStudent, EnrollmentTabCache, TotalEnrollmentByCourse
from student.models import CourseEnrollment

log = logging.getLogger(__name__)


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
        'minute': '*/1',
        'hour': '*',
        'day_of_week': '*',
        'day_of_month': '*',
        'month_of_year': '*',
    }
)


@periodic_task(run_every=crontab(**cron_settings))
def enrollment_collector_date():
    last_cachce = EnrollmentByStudent.objects.all().order_by('-last_update')
    if last_cachce.exists():
        last_update = last_cachce.first().last_update
    else:
        last_update = datetime(2000, 01, 01, 0, 0)
    enrollments_history = (CourseEnrollment.history
        .filter(~Q(history_type='+'))
        .filter(history_date__gt=last_update)
        .values("history_date", "is_active", "user", "course_id")
        .order_by('history_date')
    )
    users_state = {
        (u['student'], u['course_id']): {'last_update': u['last_update'], 'state': u['state']}
        for u in EnrollmentByStudent.objects.all().values("course_id", "student", "last_update", "state", )
    }
    total_stat = {
        t['course_id']: t['total'] for t in TotalEnrollmentByCourse.objects.all().values("course_id", "total", )
    }
    result_stat = {}
    for e in enrollments_history:
        key = e['user'], e['course_id']
        if key in users_state and users_state[key]['state'] == e['is_active']:
            continue
        users_state[key] = {
            'last_update': e['history_date'],
            'state': e['is_active'],
        }
        total_key = e['history_date'].date(), e['course_id']
        if total_key not in result_stat:
            result_stat[total_key] = {
                'unenroll': 0,
                'enroll': 0,
                'total': 0,
            }
            if e['course_id'] not in total_stat:
                total_stat[e['course_id']] = 0
        unenroll = 1 if e['is_active'] == 0 else 0
        enroll = 1 if e['is_active'] == 1 else 0
        total_stat[e['course_id']] += (enroll - unenroll)
        result_stat[total_key]['unenroll'] += unenroll
        result_stat[total_key]['enroll'] += enroll
        result_stat[total_key]['total'] = total_stat[e['course_id']]

    with transaction.atomic():
        for (user, course), value in users_state.iteritems():
            EnrollmentByStudent.objects.update_or_create(
                course_id=CourseKey.from_string(course), student_id=user,
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

        for (course,total) in total_stat.iteritems():
            TotalEnrollmentByCourse.objects.update_or_create(
                course_id=CourseKey.from_string(course),
                defaults={
                    'total': total,
                },
            )
