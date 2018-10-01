"""
Gradebook sub-tab module.
"""
from collections import OrderedDict
import json

from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from rg_instructor_analytics.models import GradeStatistic
from rg_instructor_analytics.utils.decorators import instructor_access_required


class GradebookView(View):
    """
    Gradebook API view.

    Source: modulestore (MongoDB) periodic task
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(GradebookView, self).dispatch(*args, **kwargs)

    @staticmethod
    def post(request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        try:
            filter_string = request.POST.get('filter')
            stats_course_id = request.POST.get('course_id')
            course_key = CourseKey.from_string(stats_course_id)

        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        enrolled_students = GradeStatistic.objects.filter(course_id=course_key)
        if filter_string:
            enrolled_students = enrolled_students.filter(
                Q(student__username__icontains=filter_string) |
                Q(student__first_name__icontains=filter_string) |
                Q(student__last_name__icontains=filter_string) |
                Q(student__email__icontains=filter_string)
            )
        enrolled_students = enrolled_students\
            .order_by('student__username')\
            .values('student__username', 'exam_info')

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
            }
        )
