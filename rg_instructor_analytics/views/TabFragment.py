"""
Module for tab fragment.
"""
from time import mktime

from django.conf import settings
from django.http import Http404
from web_fragments.fragment import Fragment
from web_fragments.views import FragmentView

from courseware.courses import get_course_by_id
from edxmako.shortcuts import render_to_string
from rg_instructor_analytics.utils.AccessMixin import AccessMixin
from student.models import CourseAccessRole

JS_URL = '{static_url}rg_instructor_analytics/js/'.format(static_url=settings.STATIC_URL)
CSS_URL = '{static_url}rg_instructor_analytics/css/'.format(static_url=settings.STATIC_URL)


class InstructorAnalyticsFragmentView(AccessMixin, FragmentView):
    """
    Fragment for render tab.
    """

    def get_enroll_info(self, course):
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
        avalibel_courses = CourseAccessRole.objects.filter(user=user, role__in=['instructor', 'staff'])
        result = []
        for record in avalibel_courses:
            try:
                result.append(get_course_by_id(record.course_id, depth=0))
            except Http404:
                continue
        return result

    def process(self, request, **kwargs):
        """
        Render tab fragment.
        """
        course = kwargs['course']
        available_courses = self.get_avalibel_courses(request.user)
        # import ipdb;ipdb.set_trace()
        print(available_courses)

        context = {
            'course': course,
            'enroll_info': self.get_enroll_info(course),
            'available_courses': [str(c.id) for c in available_courses]
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
