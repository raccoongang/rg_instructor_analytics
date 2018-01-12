"""
Module for gradebook subtab.
"""
from django.contrib.auth.models import User
from django.db.models import Q
from django.http.response import JsonResponse
from django.utils.translation import ugettext as _
from django.views.generic import View
from xmodule.modulestore.django import modulestore

from rg_instructor_analytics.utils.AccessMixin import AccessMixin

try:
    from lms.djangoapps.grades.new.course_grade_factory import CourseGradeFactory
except Exception:
    from lms.djangoapps.grades.new.course_grade import CourseGradeFactory


class GradebookView(AccessMixin, View):
    """
    Api for gradebook.
    """

    def get_grades_values(self, grade_info):
        """Return percent value of the student grade."""
        result = [int(g['percent'] * 100.0) for g in grade_info['section_breakdown']]
        result.append(int(grade_info['percent'] * 100.0))
        return result

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        filter_string = request.POST['filter']

        course_key = kwargs['course_key']
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
        )
        if filter_string:
            enrolled_students = enrolled_students.filter(
                Q(username__icontains=filter_string) |
                Q(first_name__icontains=filter_string) |
                Q(last_name__icontains=filter_string) |
                Q(email__icontains=filter_string)
            )
        enrolled_students = enrolled_students.order_by('username').select_related("profile")

        with modulestore().bulk_operations(course_key):
            student_info = [
                {
                    'username': student.username,
                    'id': student.id,
                    'grades': self.get_grades_values(CourseGradeFactory().create(student, kwargs['course']).summary)
                }
                for student in enrolled_students
            ]
            exam_names = []
            if len(enrolled_students) > 0:
                exam_names = [
                    g['label']
                    for g in CourseGradeFactory().create(enrolled_students[0], kwargs['course'])
                                                 .summary['section_breakdown']
                ]
                exam_names.append(_('total'))
        return JsonResponse(data={'student_info': student_info, 'exam_names': exam_names})
