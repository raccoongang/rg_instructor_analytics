"""
Module for enrollment subtab.
"""
from django.conf import settings
from django.http.response import JsonResponse
from django.views.generic import View

from celery.result import AsyncResult
from celery import states

from rg_instructor_analytics.utils.AccessMixin import AccessMixin
from rg_instructor_analytics.tasks import enrollment_collector_date_v2

JS_URL = '{static_url}rg_instructor_analytics/js/'.format(static_url=settings.STATIC_URL)
CSS_URL = '{static_url}rg_instructor_analytics/css/'.format(static_url=settings.STATIC_URL)

QUESTUIN_SELECT_TYPE = 'select'
QUESTUIN_MULTI_SELECT_TYPE = 'multySelect'


class EnrollmentStatisticView(AccessMixin, View):
    """
    Api for getting enrollment statistic.
    """

    def process(self, request, **kwargs):
        """
        Process post request for this view.
        """
        task_id = request.POST.get('task_id')
        course_id = request.POST.get('course_id')
        reset_cohort = request.POST.get('reset_cohort')
        cohort_name = None if reset_cohort else request.POST.get('cohort')
        if task_id:
            task_state = AsyncResult(task_id).state
            if task_state == states.SUCCESS:
                return JsonResponse({'data': AsyncResult(task_id).result, 'state': task_state})
            return JsonResponse(data={'state': task_state})
        from_timestamp = int(request.POST['from'])
        to_timestamp = int(request.POST['to'])
        task = enrollment_collector_date_v2.apply_async(args=(course_id, cohort_name, from_timestamp, to_timestamp))
        return JsonResponse({'state': AsyncResult(task.task_id).state, 'task_id': task.task_id})
