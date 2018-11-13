"""
Module for tab fragment.
"""
import json
import sys
from time import mktime

from django.http import Http404, HttpResponseBadRequest
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rg_instructor_analytics_log_collector.models import EnrollmentByDay
from web_fragments.fragment import Fragment

from courseware.courses import get_course_by_id
from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from rg_instructor_analytics.utils import resource_string
from rg_instructor_analytics.utils.decorators import instructor_access_required
from student.models import CourseAccessRole

# NOTE(flying-pi) reload(sys) is used for restore method `setdefaultencoding`,
# which set flag PYTHONIOENCODING to utf8.
reload(sys)
sys.setdefaultencoding('utf8')


class InstructorAnalyticsFragmentView(EdxFragmentView):
    """
    Fragment for render tab.
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(InstructorAnalyticsFragmentView, self).dispatch(*args, **kwargs)

    def render_to_fragment(self, request, *args, **kwargs):
        """
        Render tab fragment.
        """
        try:
            course_key = CourseKey.from_string(kwargs.get('course_id'))
            course = get_course_by_id(course_key)
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        available_courses = [
            {
                'course_id': str(user_course.id),
                'course_name': str(user_course.display_name),
                'is_current': course == user_course,
            }
            for user_course in self.get_available_courses(request.user)
        ]

        enroll_info = {
            str(course_item.id): self.get_enroll_info(course_item)
            for course_item in self.get_available_courses(request.user)
        }

        course_dates_info = {
            str(course_item.id): self.get_course_dates_info(course_item)
            for course_item in self.get_available_courses(request.user)
        }

        context = {
            'course': course,
            'enroll_info': json.dumps(enroll_info),
            'available_courses': available_courses,
            'course_dates_info': json.dumps(course_dates_info),
        }

        html = render_to_string('rg_instructor_analytics/instructor_analytics_fragment.html', context)
        fragment = Fragment(html)
        fragment.add_css(resource_string("css/instructor_analytics.css"))

        fragment.add_javascript(resource_string("js/utils.js"))
        fragment.add_javascript(resource_string("js/tab.js"))
        fragment.add_javascript(resource_string("js/tab-holder.js"))
        fragment.add_javascript(resource_string("js/enrollment-tab.js"))
        fragment.add_javascript(resource_string("js/activity-tab.js"))
        fragment.add_javascript(resource_string("js/problem-tab.js"))
        fragment.add_javascript(resource_string("js/funnel-tab.js"))
        fragment.add_javascript(resource_string("js/gradebook-tab.js"))
        fragment.add_javascript(resource_string("js/clusters-tab.js"))
        fragment.add_javascript(resource_string("js/suggestions-tab.js"))
        fragment.add_javascript(resource_string("js/base.js"))

        return fragment

    @staticmethod
    def get_enroll_info(course):
        """
        Return enroll_start and enroll_end for given course.
        """
        enrollment_by_day = EnrollmentByDay.objects.filter(course=course.id).order_by('day').first()
        enroll_start = enrollment_by_day and enrollment_by_day.day
        return {
            'enroll_start': mktime(enroll_start.timetuple()) if enroll_start else 'null',
        }

    @staticmethod
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

    @staticmethod
    def get_course_dates_info(course):
        """
        Return course_start and course_is_started for given course.
        """
        return {
            'course_start': mktime(course.start.timetuple()) if course.start else 'null',
            'course_is_started': False if course.start and course.start > timezone.now() else True
        }
