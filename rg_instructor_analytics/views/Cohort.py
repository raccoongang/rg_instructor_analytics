"""
Clusters sub-tab module.
"""
import math

from django.contrib.auth.models import User
from django.http.response import HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from rg_instructor_analytics import tasks
from rg_instructor_analytics.models import GradeStatistic
from rg_instructor_analytics.utils.decorators import instructor_access_required


class CohortView(View):
    """
    Cohorts statistics API view.
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(CohortView, self).dispatch(*args, **kwargs)

    def post(self, request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        stats_course_id = request.POST.get('course_id')

        try:
            course_key = CourseKey.from_string(stats_course_id)
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        grade_stats = (
            GradeStatistic.objects
            .filter(course_id=course_key)
            .values('student_id', 'student__username', 'total')
        )

        if not grade_stats:
            return JsonResponse(data={'labels': [], 'values': [], 'cohorts': []})

        cohorts = self.generate_cohort_by_mean_and_dispersion([
            {
                'id': grade['student_id'],
                'username': grade['student__username'],
                'grade': grade['total']
            } for grade in grade_stats
        ])

        labels = []
        for i, cohort in enumerate(cohorts):
            prev_cohort = cohorts[i - 1]
            if cohort['max_progress'] == 0:
                labels.append(_('zero progress'))
            else:
                labels.append(
                    _('from {} % to {} %').format(prev_cohort['max_progress'], cohort['max_progress'])
                )
        values = [info['percent'] for info in cohorts]

        return JsonResponse(data={'labels': labels, 'values': values, 'cohorts': cohorts})

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
        thresholds = [0]

        def add_thresholds(value):
            """
            Prevent invalid values of the threshold.

            Invalid values - negative, positive and more than 1 or values with diff less than 1 percent.
            """
            if value < 0.0 or value > 1.0 or abs(thresholds[-1] - value) < (1.0 / 100.0):
                return
            thresholds.append(value)

        add_thresholds(0.0)
        add_thresholds(mean - 3 * s)
        add_thresholds(mean - 0.5 * s)
        add_thresholds(mean + 0.5 * s)
        add_thresholds(mean + 3 * s)
        add_thresholds(1.0)

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


class CohortSendMessage(View):
    """
    Endpoint for sending email message.
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(CohortSendMessage, self).dispatch(*args, **kwargs)

    def post(self, request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        users_ids = request.POST.get('users_ids')
        email_subject = request.POST.get('subject')
        email_body = request.POST.get('body')

        try:
            if users_ids is None:
                raise ValueError
        except ValueError:
            return HttpResponseBadRequest(_("No users provided."))

        users_ids_list = [int(id) for id in users_ids.split(',') if id != '']

        users_emails = [
            str(email) for email in User.objects.filter(id__in=users_ids_list).values_list('email', flat=True)
        ]

        tasks.send_email_to_cohort.delay(
            subject=email_subject,
            message=email_body,
            students=users_emails
        )
        return JsonResponse({'status': 'ok'})
