"""
Enrollment stats sub-tab module.
"""
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rg_instructor_analytics_log_collector.models import EnrollmentByDay

from rg_instructor_analytics.utils.decorators import instructor_access_required

JS_URL = '{static_url}rg_instructor_analytics/js/'.format(static_url=settings.STATIC_URL)
CSS_URL = '{static_url}rg_instructor_analytics/css/'.format(static_url=settings.STATIC_URL)

QUESTUIN_SELECT_TYPE = 'select'
QUESTUIN_MULTI_SELECT_TYPE = 'multySelect'


class EnrollmentStatisticView(View):
    """
    Enrollment stats API view.

    Data source: EnrollmentByDay DB model (rg_analytics_collector).
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(EnrollmentStatisticView, self).dispatch(*args, **kwargs)

    @staticmethod
    def get_last_state(course_key, date):
        """
        Get the last available Enrollments statistics before the date.

        :param course_key: (str) Edx course id
        :param date: (DateTime) base date
        :return: (dict) with count of `unenrolled`, `enrolled` and total users.
        For example: `{'unenrolled': 1, 'enrolled': 2, 'total': 3}`
        """
        last_state = (
            EnrollmentByDay.objects
            .filter(course=course_key, day__lt=date)
            .values('unenrolled', 'enrolled', 'total')
            .first()
        )
        return last_state or {'unenrolled': 0, 'enrolled': 0, 'total': 0}

    @staticmethod
    def get_state_for_period(course_key, cohort_id, from_date, to_date):
        """
        Get Enrollments stats for the date range.

        :param course_key: (str) Edx course id
        :param from_date: (DateTime) start range date
        :param to_date: (DateTime) end range date
        :return: list of dicts || empty list
        """
        return (
            EnrollmentByDay.objects
            .filter(course=course_key, cohort_id=cohort_id, day__range=(from_date, to_date))
            .values('unenrolled', 'enrolled', 'total', 'day')
            .order_by('day')
        )

    @staticmethod
    def get_daily_stats_for_course(from_timestamp, to_timestamp, course_key, cohort_id):  # get_day_course_stats
        """
        Provide statistic, which contains: dates in unix-time, count of enrolled users, unenrolled and total.

        Return map with next keys: dates - store list of dates in unix-time, total - store list of active users
        for given day (enrolled users - unenrolled),  enrol - store list of enrolled user for given day,
        unenroll - store list of unenrolled user for given day.
        """
        from_date = datetime.fromtimestamp(from_timestamp).date()
        to_date = datetime.fromtimestamp(to_timestamp).date()

        previous_info = EnrollmentStatisticView.get_last_state(course_key, from_date)

        dates_total = [from_date]
        counts_total = [previous_info['total']]

        dates_enroll = []
        counts_enroll = []

        dates_unenroll = []
        counts_unenroll = []

        def insert_new_stat_item(count, date, counts_list, dates_list):
            if count == 0:
                return

            yesterday = date - timedelta(1)
            if yesterday >= from_date and not (len(dates_list) > 0 and dates_list[-1] == yesterday):
                counts_list.append(0)
                dates_list.append(yesterday)

            if len(dates_list) > 0 and dates_list[-1] == date:
                counts_list[-1] = count
            else:
                counts_list.append(count)
                dates_list.append(date)

            tomorrow = date + timedelta(1)
            if tomorrow <= to_date:
                counts_list.append(0)
                dates_list.append(tomorrow)

        for data in EnrollmentStatisticView.get_state_for_period(course_key, cohort_id, from_date, to_date):
            dates_total.append(data['day'])
            counts_total.append(data['total'])

            insert_new_stat_item(data['enrolled'], data['day'], counts_enroll, dates_enroll)

            insert_new_stat_item(data['unenrolled'], data['day'], counts_unenroll, dates_unenroll)

        dates_total.append(to_date)
        counts_total.append(counts_total[-1])

        nticks_y1 = max(counts_total) - min(counts_total) if counts_total else 0
        counts_enroll_unenroll = counts_enroll + counts_unenroll
        nticks_y2 = max(counts_enroll_unenroll) if counts_enroll_unenroll else 0

        dates_delta = to_date - from_date

        customize_xticks = True if dates_delta.days <= 5 else False  # x-axis "Date"
        customize_y1ticks = True if nticks_y1 <= 3 else False  # y-axis "Total"
        customize_y2ticks = True if nticks_y2 <= 3 else False  # y-axis "Enrolled/Unenrolled"

        return {
            'dates_total': dates_total, 'counts_total': counts_total,
            'dates_enroll': dates_enroll, 'counts_enroll': counts_enroll,
            'dates_unenroll': dates_unenroll, 'counts_unenroll': counts_unenroll,
            'customize_xticks': customize_xticks,
            'customize_y1ticks': customize_y1ticks, 'customize_y2ticks': customize_y2ticks,
            'nticks_y1': nticks_y1, 'nticks_y2': nticks_y2,
        }

    def post(self, request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        try:
            from_timestamp = int(request.POST['from'])
            to_timestamp = int(request.POST['to'])

            cohort_id = request.POST.get('cohort_id')
            stats_course_id = request.POST.get('course_id')
            course_key = CourseKey.from_string(stats_course_id)

        except MultiValueDictKeyError:
            return HttpResponseBadRequest(_("`from`, `to`, `course_id` are the must."))
        except TypeError:
            return HttpResponseBadRequest(_("Invalid date range."))
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        return JsonResponse(
            data=self.get_daily_stats_for_course(from_timestamp, to_timestamp, course_key, cohort_id)
        )
