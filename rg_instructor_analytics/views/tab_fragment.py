"""
Module for tab fragment.
"""
import json
import sys
from time import mktime

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render_to_response
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from instructor.views.api import require_level
from opaque_keys.edx.keys import CourseKey
from rg_instructor_analytics_log_collector.models import EnrollmentByDay
from util.views import ensure_valid_course_key

from courseware.courses import get_course_by_id
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from rg_instructor_analytics.models import CohortReportTabsConfig, InstructorTabsConfig
from student.models import CourseAccessRole

# NOTE(flying-pi) reload(sys) is used for restore method `setdefaultencoding`,
# which set flag PYTHONIOENCODING to utf8.
reload(sys)
sys.setdefaultencoding('utf8')


TABS = (
    {
        'field': 'enrollment_stats',
        'class': 'enrollment-stats',
        'section': 'enrollment_stats',
        'title': _('Enrollment stats'),
        'template': 'enrollment_stats.html'
    },
    {
        'field': 'activities',
        'class': 'activity',
        'section': 'activity',
        'title': _('Activities'),
        'template': 'activity.html'
    },
    {
        'field': 'problems',
        'class': 'problems',
        'section': 'problems',
        'title': _('Problems'),
        'template': 'problems.html'
    },
    {
        'field': 'students_info',
        'class': 'gradebook',
        'section': 'gradebook',
        'title': _('Students\' Info'),
        'template': 'gradebook.html'
    },
    {
        'field': 'clusters',
        'class': 'cohort',
        'section': 'cohort',
        'title': _('Clusters'),
        'template': 'cohort.html'
    },
    {
        'field': 'progress_funnel',
        'class': 'funnel',
        'section': 'cohort',
        'title': _('Progress Funnel'),
        'template': 'funnel.html'
    },
    {
        'field': 'suggestions',
        'class': 'suggestion',
        'section': 'cohort',
        'title': _('Suggestions'),
        'template': 'suggestion.html'
    },
)


def get_enroll_info(course):
    """
    Return enroll_start for given course.
    """
    enrollment_by_day = EnrollmentByDay.objects.filter(course=course.id).order_by('day').first()
    enroll_start = enrollment_by_day and enrollment_by_day.day

    return {
        'enroll_start': mktime(enroll_start.timetuple()) if enroll_start else 'null',
    }


def get_available_courses(user):
    """
    Return courses, available for the given user.
    """
    result = []
    # For staff user we need return all available courses on platform.
    if True:
        available_courses = CourseOverview.objects.all()
        for course in available_courses:
            try:
                result.append(get_course_by_id(course.id, depth=0))
            except Http404:
                continue
    # Return courses, where user has permission as instructor of staff
    else:
        available_courses = CourseAccessRole.objects.filter(user=user, role__in=['instructor', 'staff'])
        exist_courses_id = []
        for record in available_courses:
            try:
                course = get_course_by_id(record.course_id, depth=0)
                course_id = str(course.id)
                if course_id not in exist_courses_id:
                    result.append(course)
                    exist_courses_id.append(course_id)
            except Http404:
                continue
    return result


def get_course_dates_info(course):
    """
    Return course_start and course_is_started for given course.
    """
    return {
        'course_start': mktime(course.start.timetuple()) if course.start else 'null',
        'course_is_started': False if course.start and course.start > timezone.now() else True
    }


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@ensure_valid_course_key
@require_level('staff')
def instructor_analytics_dashboard(request, course_id):
    """
    Display the instructor dashboard for a course.
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key, depth=0)

    enroll_info = {
        str(course_item.id): get_enroll_info(course_item)
        for course_item in get_available_courses(request.user)
    }

    available_courses = [
        {
            'course_id': str(user_course.id),
            'course_name': str(user_course.display_name),
            'is_current': course == user_course,
        }
        for user_course in get_available_courses(request.user)
    ]

    course_dates_info = {
        str(course_item.id): get_course_dates_info(course_item)
        for course_item in get_available_courses(request.user)
    }

    enabled_tabs = InstructorTabsConfig.tabs_for_user(request.user)
    tabs = [t for t in TABS if t['field'] in enabled_tabs]

    context = {
        'tabs': tabs,
        'course': course,
        'enroll_info': json.dumps(enroll_info),
        'available_courses': available_courses,
        'course_dates_info': json.dumps(course_dates_info),
    }
    return render_to_response('rg_instructor_analytics/instructor_analytics_fragment.html', context)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@ensure_valid_course_key
@login_required
def cohort_report_dashboard(request, course_id):
    """
    Display the cohort report for a course.
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key, depth=0)
    user = request.user

    # check
    cohorts = user.profile.cohort_leader.all()

    # check
    available_cohorts = [
        {
            'cohort_id': str(user_cohort.course_user_group.id),
            'course_id': str(user_cohort.course_user_group.course_id),
            'cohort_name': "{}: {}".format(str(user_cohort.course_user_group.name), get_course_by_id(user_cohort.course_user_group.course_id).display_name),
            'is_current': cohorts.filter(course_user_group__course_id=course_key).first() == user_cohort,
        }
        for user_cohort in cohorts
    ]

    course_dates_info = {
        str(course_item.id): get_course_dates_info(course_item)
        for course_item in get_available_courses(request.user)
    }

    def _update_templates(tab):
        new_tab = tab.copy()
        if tab['field'] == 'students_info':
            new_tab['template'] = 'cohort_gradebook.html'
        return new_tab

    enabled_tabs = ['students_info', 'progress_funnel']
    tabs = [_update_templates(t) for t in TABS if t['field'] in enabled_tabs]

    context = {
        'tabs': tabs,
        'course': course,
        'available_cohorts': available_cohorts,
        'course_dates_info': json.dumps(course_dates_info),
    }

    return render_to_response('rg_instructor_analytics/cohort_report_fragment.html', context)
