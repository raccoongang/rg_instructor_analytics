"""
Module for cohort subtab.
"""
import math

from django.contrib.auth.models import User
from django.http.response import JsonResponse
from django.utils.translation import ugettext as _
from django.views.generic import View
from xmodule.modulestore.django import modulestore

from rg_instructor_analytics import tasks
from rg_instructor_analytics.utils.AccessMixin import AccessMixin

try:
    from lms.djangoapps.grades.new.course_grade_factory import CourseGradeFactory
except Exception:
    from lms.djangoapps.grades.new.course_grade import CourseGradeFactory


class CohortView(AccessMixin, View):
    """
    Api for cohort statistic.
    """

    @staticmethod
    def generate_cohort_by_mean_and_dispersion(student_info):
        """
        Generate cohort.

        :param student_info [
                    {
                        'id': 'user id',
                        'username': 'user name',
                        'grade': 'user grade'
                    }
                    .....
                ]

        Generate cohort for next algorithm:
        1. Calculate mean(m) and standart deviation(s) of total grade [0,1]
        2. Set thresholds 0:(m - 3s):(m - 0.5s):(m + 0.5s):(m - 3s):1
        3. Return [
            {
                'max_progress': 'max progress in this cohort',
                'students_id': 'list of hte students ids',
                'students_username': 'list of hte students usernames',
                'percent': 'percent of this cohort in course enrollments'
            } for t in thresholds
        ]
        """
        marks = [i['grade'] for i in student_info]
        mark_count = len(marks)
        mean = sum(marks) / mark_count
        s = math.sqrt(sum([(x - mean) ** 2 for x in marks]) / mark_count)
        thresholds = []
        if mean - 3 * s > 0:
            thresholds.append(mean - 3 * s)
        if mean - 0.5 * s > 0:
            thresholds.append(mean - 0.5 * s)
        if mean + 0.5 * s < 1:
            thresholds.append(mean + 0.5 * s)
        if mean + 3 * s < 1:
            thresholds.append(mean + 3 * s)
        thresholds.append(1)
        if thresholds[0] != 0:
            thresholds.insert(0, 0)
        return CohortView.split_students(student_info, thresholds)

    @staticmethod
    def split_students(student_info, thresholds):
        """
        Split student by thresholds.

        Return Return [
            {
                'max_progress': 'max progress in this cohort',
                'students_id': 'list of hte students ids',
                'students_username': 'list of hte students usernames',
                'percent': 'percent of this cohort in course enrollments'
            } for t in thresholds
        ]
        """
        gistogram = {t: {'students_id': [], 'students_names': [], 'count': 0} for t in thresholds}
        for s in student_info:
            for t in thresholds:
                if (s['grade'] < t) or (s['grade'] == t and (t in [0, 1])):
                    gistogram[t]['students_id'].append(s['id'])
                    gistogram[t]['students_names'].append(s['username'])
                    gistogram[t]['count'] += 1
                    break

        student_count = float(len(student_info))

        return [
            {
                'max_progress': int(t * 100.0),
                'students_id': gistogram[t]['students_id'],
                'students_username': gistogram[t]['students_names'],
                'percent': int(float(gistogram[t]['count']) / student_count * 100.0)
            } for t in thresholds
        ]

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        course_key = kwargs['course_key']
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
        )
        enrolled_students = enrolled_students.order_by('username').select_related("profile")

        with modulestore().bulk_operations(course_key):
            cohorts = self.generate_cohort_by_mean_and_dispersion(
                [
                    {
                        'id': student.id,
                        'username': student.username,
                        'grade': CourseGradeFactory().create(student, kwargs['course']).summary['percent']
                    }
                    for student in enrolled_students
                ]
            )

        labels = []
        for i in range(len(cohorts)):
            if cohorts[i]['max_progress'] == 0:
                labels.append(_('zero progress'))
            else:
                labels.append(
                    _('from ') + str(cohorts[i - 1]['max_progress']) + ' %' +
                    _(' to ') + str(cohorts[i]['max_progress']) + ' %'
                )
        values = [i['percent'] for i in cohorts]
        return JsonResponse(data={'labels': labels, 'values': values, 'cohorts': cohorts})


class CohortSendMessage(AccessMixin, View):
    """
    Endpoint for sending email message.
    """

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        tasks.send_email_to_cohort(
            subject=request.POST['subject'],
            message=request.POST['body'],
            students=User.objects.filter(id__in=request.POST['users_ids'].split(',')).values_list('email', flat=True)
        )
        return JsonResponse({'status': 'ok'})
