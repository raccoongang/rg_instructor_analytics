"""
Module for enrollment subtab.
"""
from datetime import datetime

from django.conf import settings
from django.http.response import JsonResponse
from django.views.generic import View

from rg_instructor_analytics.models import EnrollmentTabCache
from rg_instructor_analytics.utils.AccessMixin import AccessMixin


JS_URL = '{static_url}rg_instructor_analytics/js/'.format(static_url=settings.STATIC_URL)
CSS_URL = '{static_url}rg_instructor_analytics/css/'.format(static_url=settings.STATIC_URL)

QUESTUIN_SELECT_TYPE = 'select'
QUESTUIN_MULTI_SELECT_TYPE = 'multySelect'


class EnrollmentStatisticView(AccessMixin, View):
    """
    Api for getting enrollment statistic.
    """

    @staticmethod
    def get_state_before(course_key, date):
        """
        Provide dict with count of  unenroll, enroll and total users.

        For example `{'unenroll': 1, 'enroll': 2, 'total': 3}`
        """
        previous_stat = (
            EnrollmentTabCache.objects
            .filter(course_id=course_key, created__lt=date)
            .values('unenroll', 'enroll', 'total')
            .order_by('-created')
        )
        return previous_stat.first() if previous_stat.exists() else {'unenroll': 0, 'enroll': 0, 'total': 0}

    @staticmethod
    def get_state_in_period(course_key, from_date, to_date):
        """
        Provide list of dict with count of  unenroll, enroll, total and change date.
        """
        enrollment_stat = (
            EnrollmentTabCache.objects
            .filter(course_id=course_key, created__range=(from_date, to_date))
            .values('unenroll', 'enroll', 'total', 'created')
            .order_by('created')
        )
        return enrollment_stat

    @staticmethod
    def get_statistic_per_day(from_timestamp, to_timestamp, course_key):
        """
        Provide statistic, which contains: dates in unix-time, count of enrolled users, unenrolled and total.

        Return map with next keys: dates - store list of dates in unix-time, total - store list of active users
        for given day (enrolled users - unenrolled),  enrol - store list of enrolled user for given day,
        unenroll - store list of unenrolled user for given day.
        """
        from_date = datetime.fromtimestamp(from_timestamp).date()
        to_date = datetime.fromtimestamp(to_timestamp).date()

        previous_info = EnrollmentStatisticView.get_state_before(course_key, from_date)

        dates = [from_date]
        counts_total = [previous_info['total']]
        counts_enroll = [0]
        counts_unenroll = [0]

        for e in EnrollmentStatisticView.get_state_in_period(course_key, from_date, to_date):
            dates.append(e['created'])
            counts_total.append(e['total'])
            counts_enroll.append(e['enroll'])
            counts_unenroll.append(e['unenroll'])

        dates.append(to_date)
        counts_total.append(counts_total[-1])
        counts_enroll.append(0)
        counts_unenroll.append(0)

        return {'dates': dates, 'total': counts_total, 'enroll': counts_enroll, 'unenroll': counts_unenroll, }

    def process(self, request, **kwargs):
        """
        Process post request for this view.
        """
        from_timestamp = int(request.POST['from'])
        to_timestamp = int(request.POST['to'])

        return JsonResponse(data=self.get_statistic_per_day(from_timestamp, to_timestamp, kwargs['course_key']))
