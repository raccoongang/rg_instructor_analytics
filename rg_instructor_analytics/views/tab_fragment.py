"""
Module for tab fragment.
"""
import json
import sys
from time import mktime

from django.http import Http404
from django.shortcuts import render_to_response
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey
from rg_instructor_analytics_log_collector.models import EnrollmentByDay
from courseware.courses import get_course_by_id
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseAccessRole
from instructor.views.api import require_level
from util.views import ensure_valid_course_key

from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie

# NOTE(flying-pi) reload(sys) is used for restore method `setdefaultencoding`,
# which set flag PYTHONIOENCODING to utf8.
reload(sys)
sys.setdefaultencoding('utf8')


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
    if user.is_staff:
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

    context = {
        'course': course,
        'enroll_info': json.dumps(enroll_info),
        'available_courses': available_courses,
        'course_dates_info': json.dumps(course_dates_info),
    }

    return render_to_response('rg_instructor_analytics/instructor_analytics_fragment.html', context)
