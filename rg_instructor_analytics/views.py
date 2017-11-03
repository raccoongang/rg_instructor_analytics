from datetime import datetime
import logging
from time import mktime

from django.db.models import Count
from django.db.models.expressions import RawSQL
from django.db.models.fields import DateField
from django.http.response import JsonResponse, HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.views.generic import View
from django.conf import settings

from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_by_id
from courseware.access import has_access
from student.models import CourseEnrollment
from opaque_keys import InvalidKeyError

from web_fragments.fragment import Fragment

log = logging.getLogger(__name__)

JS_URL = '{static_url}rg_instructor_analytics/js/'.format(static_url=settings.STATIC_URL)
CSS_URL = '{static_url}rg_instructor_analytics/css/'.format(static_url=settings.STATIC_URL)


class EnrollmentStatisticView(View):

    @staticmethod
    def request_to_db_for_stats_before(course_key, date):
        """
        Makes a request to the database for getting a count of enrolled and unenrolled users.

        As result return list of maps next format: {'is_active': Boolean, 'count': Integer}
        Example of function result: [{'is_active': True, 'count': 10}, {'is_active': False, 'count': 2}]
        """
        return (
            CourseEnrollment.history
                .filter(course_id=course_key, history_date__lt=date).values('is_active')
                .annotate(count=Count('is_active')).order_by('is_active')
        )

    @staticmethod
    def get_state_before(course_key, date):
        """
        Provide tuple with count of enroll and unenroll users.

        For example - if database store 5 enrolled users and 2 unenrolled the result will be next: (5,-2)
        """
        stats = EnrollmentStatisticView.request_to_db_for_stats_before(course_key, date)
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
        Provide list of tuples(date, is_active, count)

        List contains next fields: date - day of activity, is_active - enrollment status,
        count - the number of student with given activity in given day
        """
        enrollment_query = (
            CourseEnrollment.history
                .filter(course_id=course_key, history_date__range=(from_date, to_date))
                .annotate(date=RawSQL("select DATE(history_date)", (), output_field=DateField()))
                .values("date", "is_active")
                .annotate(count=Count('date'))
                .order_by('is_active').order_by('date')
        )

        return enrollment_query

    @staticmethod
    def get_statistic_per_day(from_timestamp, to_timestamp, course_key):
        """
        Provide statistic, which contains: dates in unix-time, count of enrolled users, unenrolled and total

        Return map with next keys: dates - store list of dates in unix-time, total - store list of active users
        for given day (enrolled users - unenrolled),  enrol - store list of enrolled user for given day,
        unenroll - store list of unenrolled user for given day
        """
        from_date = datetime.fromtimestamp(from_timestamp)
        to_date = datetime.fromtimestamp(to_timestamp)

        enrollment_count, un_enrollment_count = EnrollmentStatisticView.get_state_before(course_key, from_date)
        enrollments = EnrollmentStatisticView.get_state_in_period(course_key, from_date, to_date)

        dates, counts_total, counts_enroll, counts_unenroll = [], [], [], []

        dates.append(int(from_timestamp))
        counts_total.append(enrollment_count + un_enrollment_count)
        counts_enroll.append(enrollment_count)
        counts_unenroll.append(un_enrollment_count)

        for enroll in enrollments:
            if enroll['is_active']:
                enrollment_count += enroll['count']
            else:
                un_enrollment_count -= enroll['count']

            stat_date = int(mktime(enroll['date'].timetuple()))
            if dates[-1] != stat_date:
                dates.append(stat_date)
                counts_total.append(enrollment_count + un_enrollment_count)
                counts_enroll.append(enrollment_count)
                counts_unenroll.append(un_enrollment_count)
            else:
                counts_total[-1] = enrollment_count + un_enrollment_count
                counts_enroll[-1] = enrollment_count
                counts_unenroll[-1] = un_enrollment_count

        dates.append(to_timestamp)
        counts_total.append(enrollment_count + un_enrollment_count)
        counts_enroll.append(enrollment_count)
        counts_unenroll.append(un_enrollment_count)

        return {'dates': dates, 'total': counts_total, 'enroll': counts_enroll, 'unenroll': counts_unenroll, }

    def post(self, request, course_id):
        """
        Processes post request for this view
        """
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error("Unable to find course with course key %s while getting enrollment statistic", course_id)
            return HttpResponseBadRequest()
        course = get_course_by_id(course_key, depth=0)
        if not has_access(request.user, 'staff', course):
            log.error("Enrollment statistics not available for user type `%s`", request.user)
            return HttpResponseForbidden()

        from_timestamp = int(request.POST['from'])
        to_timestamp = int(request.POST['to'])

        return JsonResponse(data=self.get_statistic_per_day(from_timestamp, to_timestamp, course_key))


class InstructorAnalyticsFragmentView(EdxFragmentView):

    def render_to_fragment(self, request, course_id=None, **kwargs):
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error("Unable to find course with course key %s while loading the Instructor Analytics Dashboard.",
                      course_id)
            return HttpResponseBadRequest()

        course = get_course_by_id(course_key, depth=0)
        if not has_access(request.user, 'staff', course):
            log.error("Statistics not available for user type `%s`", request.user)
            return HttpResponseForbidden()

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
