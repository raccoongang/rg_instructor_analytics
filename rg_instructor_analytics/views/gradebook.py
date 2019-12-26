"""
Gradebook sub-tab module.
"""
import csv
import json
from collections import OrderedDict

from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
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
            _format = request.POST.get('format', 'json')
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
        enrolled_students = enrolled_students.order_by('student__username')

        student_info = []
        students_names = []
        for student in enrolled_students:
            student_info.append(json.JSONDecoder(object_pairs_hook=OrderedDict).decode(student.exam_info))
            students_names.append([student.student.username, student.is_enrolled])

        exam_names = list(student_info[0].keys()) if len(student_info) > 0 else []

        if _format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="{}_gradebook.csv"'.format(course_key)

            writer = csv.writer(response)
            writer.writerow([_('Student')] + exam_names)
            get_grades = lambda n: [student_info[n][e] for e in exam_names]  # noqa: E731
            [writer.writerow([d[0]] + get_grades(i)) for i, d in enumerate(students_names)]

            return response

        return JsonResponse(
            data={
                'student_info': student_info,
                'exam_names': exam_names,
                'students_names': students_names,
            }
        )
