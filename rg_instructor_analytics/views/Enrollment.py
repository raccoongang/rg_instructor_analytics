"""
Module for enrollment subtab.
"""
from datetime import datetime
from time import mktime

from django.conf import settings
from django.db.models import Count, Q
from django.db.models.expressions import RawSQL
from django.db.models.fields import DateField
from django.http.response import JsonResponse
from django.views.generic import View

from rg_instructor_analytics.utils.AccessMixin import AccessMixin
from student.models import CourseEnrollment

JS_URL = '{static_url}rg_instructor_analytics/js/'.format(static_url=settings.STATIC_URL)
CSS_URL = '{static_url}rg_instructor_analytics/css/'.format(static_url=settings.STATIC_URL)

QUESTUIN_SELECT_TYPE = 'select'
QUESTUIN_MULTI_SELECT_TYPE = 'multySelect'


class EnrollmentStatisticView(AccessMixin, View):
    """
    Api for getting enrollment statistic.
    """

    @staticmethod
    def request_to_db_for_stats_before(course_key, date):
        """
        Make a request to the database for getting a count of enrolled and unenrolled users.

        As result return list of maps next format: {'is_active': Boolean, 'count': Integer}
        Example of function result: [{'is_active': True, 'count': 10}, {'is_active': False, 'count': 2}]
        """
        return (
            CourseEnrollment
            .history
            .filter(course_id=course_key, history_date__lt=date)
            .filter(~Q(history_type='+'))
            .values('is_active')
            .annotate(count=Count('is_active'))
            .order_by('is_active')
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
        Provide list of tuples(date, is_active, count).

        List contains next fields: date - day of activity, is_active - enrollment status,
        count - the number of student with given activity in given day.
        """
        enrollment_query = (
            CourseEnrollment
            .history
            .filter(course_id=course_key, history_date__range=(from_date, to_date))
            .filter(~Q(history_type='+'))
            .annotate(date=RawSQL("select DATE(history_date)", (), output_field=DateField()))
            .values("date", "is_active")
            .annotate(count=Count('date'))
            .order_by('is_active')
            .order_by('date')
        )

        return enrollment_query

    @staticmethod
    def get_statistic_per_day(from_timestamp, to_timestamp, course_key):
        """
        Provide statistic, which contains: dates in unix-time, count of enrolled users, unenrolled and total.

        Return map with next keys: dates - store list of dates in unix-time, total - store list of active users
        for given day (enrolled users - unenrolled),  enrol - store list of enrolled user for given day,
        unenroll - store list of unenrolled user for given day.
        """
        from_date = datetime.fromtimestamp(from_timestamp)
        to_date = datetime.fromtimestamp(to_timestamp)

        enrollment_count, un_enrollment_count = EnrollmentStatisticView.get_state_before(course_key, from_date)
        enrollments = EnrollmentStatisticView.get_state_in_period(course_key, from_date, to_date)

        dates, counts_total, counts_enroll, counts_unenroll = ([], [], [], [])

        total = enrollment_count + un_enrollment_count
        enrollment_count = 0
        un_enrollment_count = 0

        dates.append(int(from_timestamp))
        counts_total.append(total)
        counts_enroll.append(enrollment_count)
        counts_unenroll.append(un_enrollment_count)

        for enroll in enrollments:
            if enroll['is_active']:
                enrollment_count = enroll['count']
            else:
                un_enrollment_count = -enroll['count']

            total += enrollment_count + un_enrollment_count
            stat_date = int(mktime(enroll['date'].timetuple()))
            if dates[-1] != stat_date:
                dates.append(stat_date)
                counts_total.append(total)
                counts_enroll.append(enrollment_count)
                counts_unenroll.append(un_enrollment_count)
            else:
                counts_total[-1] = total
                counts_enroll[-1] = enrollment_count
                counts_unenroll[-1] = un_enrollment_count

        dates.append(to_timestamp)
        counts_total.append(total)
        counts_enroll.append(enrollment_count)
        counts_unenroll.append(un_enrollment_count)

        return {'dates': dates, 'total': counts_total, 'enroll': counts_enroll, 'unenroll': counts_unenroll, }

    def process(self, request, **kwargs):
        """
        Process post request for this view.
        """
        from_timestamp = int(request.POST['from'])
        to_timestamp = int(request.POST['to'])

        return JsonResponse(data=self.get_statistic_per_day(from_timestamp, to_timestamp, kwargs['course_key']))
