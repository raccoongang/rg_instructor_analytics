"""
Module for gradebook subtab.
"""
import json

from django.db.models import Q
from django.http.response import JsonResponse
from django.views.generic import View

from rg_instructor_analytics.models import GradeStatistic
from rg_instructor_analytics.utils.AccessMixin import AccessMixin


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
        enrolled_students = GradeStatistic.objects.filter(course_id=course_key)
        if filter_string:
            enrolled_students = enrolled_students.filter(
                Q(student__username__icontains=filter_string) |
                Q(student__first_name__icontains=filter_string) |
                Q(student__last_name__icontains=filter_string) |
                Q(student__email__icontains=filter_string)
            )
        enrolled_students = enrolled_students.order_by('student__username').values('student__username','exam_info')

        student_info = [json.loads(student['exam_info']) for student in enrolled_students]
        exam_names = list(student_info[0].keys()) if len(student_info) > 0 else []
        return JsonResponse(data={'student_info': student_info, 'exam_names': exam_names})
