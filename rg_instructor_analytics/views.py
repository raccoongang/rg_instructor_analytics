import logging

from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

from edxmako.shortcuts import render_to_string
from django.http import HttpResponseBadRequest
from courseware.courses import get_course_by_id

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from web_fragments.fragment import Fragment
from . import JS_URL

log = logging.getLogger(__name__)


class CalendarTabFragmentView(EdxFragmentView):

    def render_to_fragment(self, request, course_id=None, **kwargs):
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error(u"Unable to find course with course key %s while loading the Instructor Dashboard.", course_id)
            return HttpResponseBadRequest()

        course = get_course_by_id(course_key, depth=0)

        context = {
            'course': course,
        }

        log.debug(context)
        html = render_to_string('rg_instructor_analytics/instructor_analytics_fragment.html', context)
        fragment = Fragment(html)
        fragment.add_javascript_url(JS_URL)

        return fragment
