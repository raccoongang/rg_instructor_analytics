import logging

from django.http.response import HttpResponse
from django.utils.translation import ugettext_noop
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

from edxmako.shortcuts import render_to_response, render_to_string
from django.http import Http404, HttpResponseServerError
from courseware.courses import get_course_by_id, get_studio_url

from xmodule.tabs import CourseTab
from courseware.access import has_access
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from web_fragments.views import FragmentView
from web_fragments.fragment import Fragment
from . import VENDOR_CSS_URL, VENDOR_JS_URL, VENDOR_PLUGIN_JS_URL, JS_URL

log = logging.getLogger(__name__)


class CalendarTabFragmentView(EdxFragmentView):

    def render_to_fragment(self, request, course_id=None, **kwargs):
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error(u"Unable to find course with course key %s while loading the Instructor Dashboard.", course_id)
            return HttpResponseServerError()
        course = get_course_by_id(course_key, depth=0)

        sections = [

        ]

        context = {
            'course': course,
            'sections': sections
        }
        try:
            log.debug(context)
            html = render_to_string('rg_instructor_analytics/instructor_analytics_fragment.html',
                                    context)
            fragment = Fragment(html)
            return fragment

        except Exception as e:
            log.exception(e)
            return Http404()

