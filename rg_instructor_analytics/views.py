import logging

from datetime import datetime, date

import itertools
from django.http.response import JsonResponse
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView

from edxmako.shortcuts import render_to_string
from django.http import HttpResponseBadRequest
from django.views.generic import View

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from web_fragments.fragment import Fragment
from courseware.courses import get_course_by_id

from student.models import CourseEnrollment
from . import JS_URL, CSS_URL

log = logging.getLogger(__name__)


class EnrollmentStatisticView(View):

    # TODO refactoring sql request, ask Igor
    def post(self, request, course_id):
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error(u"Unable to find course with course key %s while getting enrollment statistic", course_id)
            return HttpResponseBadRequest()

        from_date = datetime.fromtimestamp(int(request.POST['from']))
        to_date = datetime.fromtimestamp(int(request.POST['to']))

        enrollment_query = CourseEnrollment.objects.filter(course_id=course_key, created__range=(from_date, to_date)) \
            .values('created').order_by('created')
        enrollment = itertools.groupby(enrollment_query, lambda x: x['created'].date())

        dates = []
        counts = []
        total_count = 0
        for day, items in enrollment:
            new_enrolls = (day - date(1970, 1, 1)).total_seconds()
            dates.append(new_enrolls)
            counts.append(total_count)
            total_count += len(list(items))
            dates.append(new_enrolls)
            counts.append(total_count)

        return JsonResponse(data={'dates': dates, 'counts': counts})


class InstructorAnalyticsFragmentView(EdxFragmentView):

    def render_to_fragment(self, request, course_id=None, **kwargs):
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error(u"Unable to find course with course key %s while loading the Instructor Dashboard.", course_id)
            return HttpResponseBadRequest()

        course = get_course_by_id(course_key, depth=0)
        enroll_start = course.enrollment_start
        if enroll_start is None:
            enroll_start = course.start

        enroll_end = course.enrollment_end
        if enroll_end is None:
            enroll_end = course.end

        enroll_info = {
            'enroll_start': (enroll_start.replace(tzinfo=None) - datetime(1970, 1, 1)).total_seconds() if (
                enroll_start is not None) else 'null',
            'enroll_end': (enroll_end.replace(tzinfo=None) - datetime(1970, 1, 1)).total_seconds() if (
                enroll_end is not None) else 'null',
        }
        context = {
            'course': course,
            'enroll_info': enroll_info
        }

        log.debug(context)
        html = render_to_string('rg_instructor_analytics/instructor_analytics_fragment.html', context)
        fragment = Fragment(html)
        fragment.add_javascript_url(JS_URL + 'instructor_analytics.js')
        fragment.add_css_url(CSS_URL + 'instructor_analytics.css')

        return fragment
