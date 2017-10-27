import logging

from datetime import datetime, date

import itertools
from time import mktime

from django.db.models import Count
from django.http.response import JsonResponse
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from parse_rest.user import login_required

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

    @staticmethod
    def get_state_before(course_key, from_date):
        """
        Provide tuple with count of enroll and unenroll users
        """
        stats = CourseEnrollment.history.filter(course_id=course_key, history_date__lt=from_date) \
            .values('is_active').annotate(count=Count('is_active')).order_by('is_active')

        enrollment_count = 0
        un_enrollment_count = 0
        for s in stats:
            if s['is_active']:
                enrollment_count += s['count']
            else:
                un_enrollment_count -= s['count']
        return enrollment_count, un_enrollment_count

    @staticmethod
    def get_state_in_period(course_key, from_date, to_date):
        """
        Provide map, where key - day of course enroll activity and value - list of activity items
        """
        enrollment_query = CourseEnrollment.history.filter(course_id=course_key,
                                                           history_date__range=(from_date, to_date)) \
            .values('history_date', 'is_active').order_by('history_date')
        return itertools.groupby(enrollment_query, lambda x: x['history_date'].date())

    # TODO refactoring sql request, ask Igor
    def post(self, request, course_id):
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error(u"Unable to find course with course key %s while getting enrollment statistic", course_id)
            return HttpResponseBadRequest()

        from_timestamp = int(request.POST['from'])
        from_date = datetime.fromtimestamp(from_timestamp)

        to_timestamp = int(request.POST['to'])
        to_date = datetime.fromtimestamp(to_timestamp)

        enrollment_count, un_enrollment_count = EnrollmentStatisticView.get_state_before(course_key, from_date)
        enrollment = EnrollmentStatisticView.get_state_in_period(course_key, from_date, to_date)

        dates, counts_total, counts_enroll, counts_unenroll = [], [], [], []

        dates.append(from_timestamp)
        counts_total.append(enrollment_count + un_enrollment_count)
        counts_enroll.append(enrollment_count)
        counts_unenroll.append(un_enrollment_count)

        for day, items in enrollment:
            for i in items:
                if i['is_active']:
                    enrollment_count += 1
                else:
                    un_enrollment_count -= 1

            new_enrolls = mktime(day.timetuple())
            dates.append(new_enrolls)
            counts_total.append(enrollment_count + un_enrollment_count)
            counts_enroll.append(enrollment_count)
            counts_unenroll.append(un_enrollment_count)

        dates.append(to_timestamp)
        counts_total.append(enrollment_count + un_enrollment_count)
        counts_enroll.append(enrollment_count)
        counts_unenroll.append(un_enrollment_count)

        data = {
            'dates': dates,
            'total': counts_total,
            'enroll': counts_enroll,
            'unenroll': counts_unenroll,
        }
        return JsonResponse(data=data)


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
            'enroll_start': mktime(enroll_start.timetuple()) if (enroll_start is not None) else 'null',
            'enroll_end': mktime(enroll_end.timetuple()) if (enroll_end is not None) else 'null',
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
