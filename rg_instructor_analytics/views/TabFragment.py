"""
Module for tab fragment.
"""
from time import mktime

from django.conf import settings
from edxmako.shortcuts import render_to_string
from web_fragments.fragment import Fragment
from web_fragments.views import FragmentView

from rg_instructor_analytics.utils.AccessMixin import AccessMixin

JS_URL = '{static_url}rg_instructor_analytics/js/'.format(static_url=settings.STATIC_URL)
CSS_URL = '{static_url}rg_instructor_analytics/css/'.format(static_url=settings.STATIC_URL)


class InstructorAnalyticsFragmentView(AccessMixin, FragmentView):
    """
    Fragment for render tab.
    """

    def process(self, request, **kwargs):
        """
        Render tab fragment.
        """
        course = kwargs['course']

        enroll_start = course.enrollment_start
        if enroll_start is None:
            enroll_start = course.start

        enroll_end = course.enrollment_end
        if enroll_end is None:
            enroll_end = course.end

        enroll_info = {
            'enroll_start': mktime(enroll_start.timetuple()) if enroll_start else 'null',
            'enroll_end': mktime(enroll_end.timetuple()) if enroll_end else 'null',
        }
        context = {
            'course': course,
            'enroll_info': enroll_info
        }

        html = render_to_string('rg_instructor_analytics/instructor_analytics_fragment.html', context)
        fragment = Fragment(html)
        fragment.add_javascript_url(JS_URL + 'Tab.js')
        fragment.add_javascript_url(JS_URL + 'CohortTab.js')
        fragment.add_javascript_url(JS_URL + 'EnrollmentTab.js')
        fragment.add_javascript_url(JS_URL + 'GradebookTab.js')
        fragment.add_javascript_url(JS_URL + 'ProblemTab.js')
        fragment.add_javascript_url(JS_URL + 'Base.js')
        fragment.add_css_url(CSS_URL + 'instructor_analytics.css')

        return fragment
