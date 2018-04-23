"""
Module for gradebook subtab.
"""
import json

from django.http.response import JsonResponse
from django.views.generic import View

from rg_instructor_analytics.utils.AccessMixin import AccessMixin


class GradebookView(AccessMixin, View):
    """
    Api for gradebook.
    """
    def process(self, request, **kwargs):
        """
        Process post request.
        """
        raw_data = ('{"student_info": [{"username": "audit", "grades": [11, 22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 2, 11, '
                    '22, 5, 3, 2, 99], "id": 3}, {"username": "audit", "grades": [11, 22, 5, 3, 2, 2, 11, 22, 5, 3, '
                    '2, 2, 11, 22, 5, 3, 2, 99], "id": 3}, {"username": "audit", "grades": [11, 22, 5, 3, 2, 2, 11, '
                    '22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 99], "id": 3}, {"username": "audit", "grades": [11, 22, 5, 3, '
                    '2, 2, 11, 22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 99], "id": 3}, {"username": "audit", "grades": [11, '
                    '22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 99], "id": 3}, {"username": "audit", '
                    '"grades": [11, 22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 99], "id": 3}, {"username": '
                    '"audit", "grades": [11, 22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 99], "id": 3}, '
                    '{"username": "audit", "grades": [11, 22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 99], '
                    '"id": 3}, {"username": "audit", "grades": [11, 22, 5, 3, 2, 2, 11, 22, 5, 3, 2, 2, 11, 22, 5, 3, '
                    '2, 99], "id": 3}], "exam_names": ["Ex 1", "Ex 2", "Ex 3", "Ex 4", "Exam 5", "Ex 6", "Ex 7", '
                    '"Ex 8", "Ex 9", "Exam 10", "Ex 11", "Ex 12", "Ex 13", "Ex 14", "Exam 15", "Ex 16", "Exam 17", '
                    '"total"]}')
        return JsonResponse(data=json.loads(raw_data))
