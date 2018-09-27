"""
Module for gradebook subtab.
"""
from collections import OrderedDict
import json
import re

from django.db.models import Q
from django.http.response import JsonResponse
from django.views.generic import View

from rg_instructor_analytics.models import GradeStatistic
from rg_instructor_analytics.utils.AccessMixin import AccessMixin
from openedx.core.djangoapps.course_groups import cohorts


class GradebookView(AccessMixin, View):
    """
    Api for gradebook.
    """

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        filter_string = request.POST['filter']

        course_key = kwargs['course_key']
        filter_args = dict(
            course_id=course_key
        )
        if kwargs['cohort']:
            filter_args.update(dict(
                student_id__in=kwargs['cohort'].users.all().values_list('id', flat=True)
            ))
        enrolled_students = GradeStatistic.objects.filter(**filter_args)
        if filter_string:
            enrolled_students = enrolled_students.filter(
                Q(student__username__icontains=filter_string) |
                Q(student__first_name__icontains=filter_string) |
                Q(student__last_name__icontains=filter_string) |
                Q(student__email__icontains=filter_string)
            )
        enrolled_students = enrolled_students.order_by('student__username').values('student__username', 'exam_info')
        student_info = [
            json.JSONDecoder(object_pairs_hook=OrderedDict).decode(student['exam_info'])
            for student in enrolled_students
        ]
        students_names = [student['student__username'] for student in enrolled_students]
        exam_names = list(student_info[0].keys()) if len(student_info) > 0 else []
        return JsonResponse(
            data={
                'student_info': student_info,
                'exam_names': exam_names,
                'students_names': students_names,
                'available_cohorts': self.course_cohorts
            }
        )
