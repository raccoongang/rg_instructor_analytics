"""
Module for tab fragment.
"""
import json
import sys
from time import mktime

from django.conf import settings
from django.http import Http404
from web_fragments.fragment import Fragment
from web_fragments.views import FragmentView

from courseware.courses import get_course_by_id
from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from rg_instructor_analytics.utils.AccessMixin import AccessMixin
from student.models import CourseAccessRole

# Used for restore method `setdefaultencoding`. It unsafe, but we need it.
reload(sys)
sys.setdefaultencoding('utf8')

JS_URL = '{static_url}rg_instructor_analytics/js/'.format(static_url=settings.STATIC_URL)
CSS_URL = '{static_url}rg_instructor_analytics/css/'.format(static_url=settings.STATIC_URL)


class InstructorAnalyticsFragmentView(AccessMixin, FragmentView):
    """
    Fragment for render tab.
    """

    def get_enroll_info(self, course):
        """
        Return enroll_start and enroll_end for given course.
        """
        enroll_start = course.enrollment_start
        if enroll_start is None:
            enroll_start = course.start

        enroll_end = course.enrollment_end
        if enroll_end is None:
            enroll_end = course.end

        return {
            'enroll_start': mktime(enroll_start.timetuple()) if enroll_start else 'null',
            'enroll_end': mktime(enroll_end.timetuple()) if enroll_end else 'null',
        }

    def get_avalibel_courses(self, user):
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

    def process(self, request, **kwargs):
        """
        Render tab fragment.
        """
        course = kwargs['course']
        available_courses = [
            {
                'course_id': str(c.id),
                'course_name': str(c.display_name),
                'is_current': course == c,
            }
            for c in self.get_avalibel_courses(request.user)
        ]

        enroll_info = {
            str(c.id): self.get_enroll_info(c)
            for c in self.get_avalibel_courses(request.user)
        }

        context = {
            'course': course,
            'enroll_info': json.dumps(enroll_info),
            'available_courses': available_courses
        }

        html = render_to_string('rg_instructor_analytics/instructor_analytics_fragment.html', context)
        fragment = Fragment(html)
        fragment.add_javascript_url(JS_URL + 'Tab.js')
        fragment.add_javascript_url(JS_URL + 'TabHolder.js')
        fragment.add_javascript_url(JS_URL + 'CohortTab.js')
        fragment.add_javascript_url(JS_URL + 'EnrollmentTab.js')
        fragment.add_javascript_url(JS_URL + 'GradebookTab.js')
        fragment.add_javascript_url(JS_URL + 'ProblemTab.js')
        fragment.add_javascript_url(JS_URL + 'FunnelTab.js')
        fragment.add_javascript_url(JS_URL + 'Suggestion.js')
        fragment.add_javascript_url(JS_URL + 'Base.js')
        fragment.add_css_url(CSS_URL + 'instructor_analytics.css')

        return fragment
