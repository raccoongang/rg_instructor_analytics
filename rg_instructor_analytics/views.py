"""
Module for tab fragment and api views.
"""
from abc import ABCMeta, abstractmethod
from datetime import datetime
from itertools import chain
import json
import logging
import math
from time import mktime

from courseware.access import has_access
from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from courseware.module_render import xblock_view
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, Sum
from django.db.models import IntegerField
from django.db.models.expressions import RawSQL
from django.db.models.fields import DateField
from django.http import HttpResponseBadRequest
from django.http.response import HttpResponseForbidden, JsonResponse
from django.utils.translation import ugettext as _
from django.views.generic import View
from edxmako.shortcuts import render_to_string
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment
from web_fragments.fragment import Fragment
from web_fragments.views import FragmentView
from xmodule.modulestore.django import modulestore

from rg_instructor_analytics import tasks

try:
    from lms.djangoapps.grades.new.course_grade_factory import CourseGradeFactory
except Exception:
    from lms.djangoapps.grades.new.course_grade import CourseGradeFactory

logging.basicConfig()

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

JS_URL = '{static_url}rg_instructor_analytics/js/'.format(static_url=settings.STATIC_URL)
CSS_URL = '{static_url}rg_instructor_analytics/css/'.format(static_url=settings.STATIC_URL)

QUESTUIN_SELECT_TYPE = 'select'
QUESTUIN_MULTI_SELECT_TYPE = 'multySelect'


class AccessMixin(object):
    """
    Base class for provide check  user permission.
    """

    __metaclass__ = ABCMeta

    group_name = 'staff'

    @abstractmethod
    def process(self, request, **kwargs):
        """
        Process allowed request.
        """
        pass

    def base_process(self, request, course_id):
        """
        Preprocess request, check permission and select course.
        """
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error("Unable to find course with course key %s while loading the Instructor Analytics Dashboard.",
                      course_id)
            return HttpResponseBadRequest()

        course = get_course_by_id(course_key, depth=0)
        if not has_access(request.user, self.group_name, course):
            log.error("Statistics not available for user type `%s`", request.user)
            return HttpResponseForbidden()

        return self.process(request, course_key=course_key, course=course, course_id=course_id)

    def post(self, request, course_id):
        """
        Overwrite base method for process post request.
        """
        return self.base_process(request, course_id)

    def render_to_fragment(self, request, course_id):
        """
        Overwrite base method for process render to fragment.
        """
        return self.base_process(request, course_id)


class EnrollmentStatisticView(AccessMixin, View):
    """
    Api for getting enrollment statistic.
    """

    @staticmethod
    def request_to_db_for_stats_before(course_key, date):
        """
        Make a request to the database for getting a count of enrolled and unenrolled users.

        As result return list of maps next format: {'is_active': Boolean, 'count': Integer}
        Example of function result: [{'is_active': True, 'count': 10}, {'is_active': False, 'count': 2}]
        """
        return (
            CourseEnrollment
            .history
            .filter(course_id=course_key, history_date__lt=date)
            .filter(~Q(history_type='+'))
            .values('is_active')
            .annotate(count=Count('is_active'))
            .order_by('is_active')
        )

    @staticmethod
    def get_state_before(course_key, date):
        """
        Provide tuple with count of enroll and unenroll users.

        For example - if database store 5 enrolled users and 2 unenrolled the result will be next: (5,-2)
        """
        stats = EnrollmentStatisticView.request_to_db_for_stats_before(course_key, date)
        enrollment_count = 0
        un_enrollment_count = 0
        for s in stats:
            if s['is_active']:
                enrollment_count += s['count']
            else:
                un_enrollment_count -= s['count']
        return enrollment_count, un_enrollment_count

    @staticmethod
    def get_state_in_period(course_key, from_date, to_date):
        """
        Provide list of tuples(date, is_active, count).

        List contains next fields: date - day of activity, is_active - enrollment status,
        count - the number of student with given activity in given day.
        """
        enrollment_query = (
            CourseEnrollment
            .history
            .filter(course_id=course_key, history_date__range=(from_date, to_date))
            .filter(~Q(history_type='+'))
            .annotate(date=RawSQL("select DATE(history_date)", (), output_field=DateField()))
            .values("date", "is_active")
            .annotate(count=Count('date'))
            .order_by('is_active')
            .order_by('date')
        )

        return enrollment_query

    @staticmethod
    def get_statistic_per_day(from_timestamp, to_timestamp, course_key):
        """
        Provide statistic, which contains: dates in unix-time, count of enrolled users, unenrolled and total.

        Return map with next keys: dates - store list of dates in unix-time, total - store list of active users
        for given day (enrolled users - unenrolled),  enrol - store list of enrolled user for given day,
        unenroll - store list of unenrolled user for given day.
        """
        from_date = datetime.fromtimestamp(from_timestamp)
        to_date = datetime.fromtimestamp(to_timestamp)

        enrollment_count, un_enrollment_count = EnrollmentStatisticView.get_state_before(course_key, from_date)
        enrollments = EnrollmentStatisticView.get_state_in_period(course_key, from_date, to_date)

        dates, counts_total, counts_enroll, counts_unenroll = ([], [], [], [])

        dates.append(int(from_timestamp))
        counts_total.append(enrollment_count + un_enrollment_count)
        counts_enroll.append(enrollment_count)
        counts_unenroll.append(un_enrollment_count)

        for enroll in enrollments:
            if enroll['is_active']:
                enrollment_count += enroll['count']
            else:
                un_enrollment_count -= enroll['count']

            stat_date = int(mktime(enroll['date'].timetuple()))
            if dates[-1] != stat_date:
                dates.append(stat_date)
                counts_total.append(enrollment_count + un_enrollment_count)
                counts_enroll.append(enrollment_count)
                counts_unenroll.append(un_enrollment_count)
            else:
                counts_total[-1] = enrollment_count + un_enrollment_count
                counts_enroll[-1] = enrollment_count
                counts_unenroll[-1] = un_enrollment_count

        dates.append(to_timestamp)
        counts_total.append(enrollment_count + un_enrollment_count)
        counts_enroll.append(enrollment_count)
        counts_unenroll.append(un_enrollment_count)

        return {'dates': dates, 'total': counts_total, 'enroll': counts_enroll, 'unenroll': counts_unenroll, }

    def process(self, request, **kwargs):
        """
        Process post request for this view.
        """
        from_timestamp = int(request.POST['from'])
        to_timestamp = int(request.POST['to'])

        return JsonResponse(data=self.get_statistic_per_day(from_timestamp, to_timestamp, kwargs['course_key']))


class ProblemHomeWorkStatisticView(AccessMixin, View):
    """
    Api for get homework`s statistic for given course.
    """

    _PARSABLE_PROBLEMS = frozenset(['multiplechoiceresponse', 'choiceresponse', 'stringresponse', 'optionresponse'])
    _LABEL = 'label'
    _DESCRIPTION = 'label'

    @staticmethod
    def academic_performance_request(course_key):
        """
        Make request to db for academic performance.

        Return list, where each item contain id of problem, average count of attempts and percent of correct answer.
        """
        attempts = RawSQL("SELECT SUBSTRING_INDEX(SUBSTRING_INDEX(state,'attempts\": ',-1),',',1)",
                          (),
                          output_field=IntegerField())

        return (
            StudentModule.objects
            .filter(course_id__exact=course_key, grade__isnull=False, module_type__exact="problem")
            .values('module_state_key')
            .annotate(attempts_avg=Avg(attempts))
            .annotate(grade_avg=Sum('grade') / Sum('max_grade'))
            .values('module_state_key', 'attempts_avg', 'grade_avg')
        )

    @classmethod
    def get_academic_performance(cls, course_key):
        """
        Provide map, where key - course and value - map with average grade and attempt.
        """
        return {
            i['module_state_key']: {'grade_avg': i['grade_avg'], 'attempts_avg': i['attempts_avg']}
            for i in cls.academic_performance_request(course_key)
        }

    def get_homework_stat(self, course_key):
        """
        Provide statistic for given course.

        :param course_key:  object, that represent course.
        :return: map with list of correct answers, attempts, list of problems for unit and names.
        Each item of given list represent one unit.
        """
        academic_performance = ProblemHomeWorkStatisticView.get_academic_performance(course_key)
        course = get_course_by_id(course_key, depth=4)
        stat = {'correct_answer': [], 'attempts': [], 'problems': [], 'names': []}
        hw_number = 0

        for subsection in chain.from_iterable(section.get_children() for section in course.get_children()):
            hw_number += 1
            stat['correct_answer'].append(0)
            stat['attempts'].append(0)
            stat['problems'].append([])
            stat['names'].append('HW{}'.format(hw_number))
            problems_in_hw = 0

            for child in chain.from_iterable(unit.get_children() for unit in subsection.get_children()):
                if child.location.category == 'problem':
                    problem_id = child.location.to_deprecated_string()
                    if problem_id in academic_performance:
                        current_performance = academic_performance[problem_id]
                        stat['correct_answer'][-1] += current_performance['grade_avg']
                        stat['attempts'][-1] += current_performance['attempts_avg']
                        problems_in_hw += 1

                    stat['problems'][-1].append(problem_id)

            if problems_in_hw > 0:
                stat['correct_answer'][-1] /= problems_in_hw
                stat['attempts'][-1] /= problems_in_hw

        return stat

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        return JsonResponse(data=self.get_homework_stat(kwargs['course_key']))


class ProblemsStatisticView(AccessMixin, View):
    """
    Api for getting statistic for each problem in unit.
    """

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        course_key = kwargs['course_key']
        problems = [course_key.make_usage_key_from_deprecated_string(p) for p in request.POST.getlist('problems')]
        stats = (
            StudentModule.objects
            .filter(module_state_key__in=problems)
            .values('module_state_key')
            .annotate(correct=Sum('grade'))
            .annotate(incorrect=Sum('grade') - Sum('max_grade'))
            .values('module_state_key', 'correct', 'incorrect')
        )
        incorrect, correct = tuple(map(list, zip(*[(int(s['incorrect'] or 0), int(s['correct'] or 0)) for s in stats])))
        return JsonResponse(data={'incorrect': incorrect, 'correct': correct})


class ProblemDetailView(AccessMixin, View):
    """
    Api for getting problem detail.
    """

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        return xblock_view(request, kwargs['course_id'], request.POST['problem'], 'student_view')


class ProblemQuestionParser:
    """
    Base class for provide statistic for question.
    """

    __metaclass__ = ABCMeta

    def __init__(self, problemID, questionID, answer_map):
        """
        Constructor.

        :param problemID: object (not string), that represent problem ID
        :param questionID: string that represent question
        :param answer_map: map for link data from data base to real data
        """
        self.answer_map = answer_map
        self.problemID = problemID
        self.questionID = questionID

    @staticmethod
    def init_statistic_object():
        """
        Provide init state for statistic.
        """
        return {}

    @abstractmethod
    def process_statistic_item(self, state, item):
        """
        Abstract method for process data form database and update statistic.
        """
        pass

    def get_statistic(self):
        """
        Provide statistic for given question.
        """
        problems = StudentModule.objects.filter(module_state_key=self.problemID, grade__isnull=False,
                                                module_type__exact="problem").values_list('state', flat=True)
        result = self.init_statistic_object()
        for p in problems:
            self.process_statistic_item(result, json.loads(p))
        return result


class ProblemSelectQuestion(ProblemQuestionParser):
    """
    Class for process question with `select` type (dropdown and single choice).
    """

    def __init__(self, problemID, questionID, answer_map):
        """
        Implement constructor.
        """
        super(ProblemSelectQuestion, self).__init__(problemID, questionID, answer_map)

    def init_statistic_object(self):
        """
        Overwrite base class.
        """
        return {'type': 'bar', 'stats': {v: 0 for v in self.answer_map.values()}}

    def process_statistic_item(self, state, item):
        """
        Overwrite base class.
        """
        state['stats'][self.answer_map[item['student_answers'][self.questionID]]] += 1


class ProblemMultiSelectQuestion(ProblemSelectQuestion):
    """
    Class for process question with `multySelect` type (question with checkboxes).
    """

    def __init__(self, problemID, questionID, answer_map):
        """
        Implement constructor.
        """
        super(ProblemMultiSelectQuestion, self).__init__(problemID, questionID, answer_map)

    def process_statistic_item(self, state, item):
        """
        Overwrite base class.
        """
        for answer in item['student_answers'][self.questionID]:
            state['stats'][self.answer_map[answer]] += 1


class ProblemQuestionView(AccessMixin, View):
    """
    Api for question statistic.
    """

    def process(self, request, **kwargs):
        """Process post request."""
        type = request.POST['type']
        questionID = request.POST['questionID']
        answer_map = json.loads(request.POST['answerMap'])
        problemID = kwargs['course_key'].make_usage_key_from_deprecated_string(request.POST['problemID'])

        if type == QUESTUIN_SELECT_TYPE:
            result = ProblemSelectQuestion(problemID, questionID, answer_map).get_statistic()
        elif type == QUESTUIN_MULTI_SELECT_TYPE:
            result = ProblemMultiSelectQuestion(problemID, questionID, answer_map).get_statistic()
        else:
            result = {}

        return JsonResponse(data=result)


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
        thresholds.append(mean - 0.5 * s)
        thresholds.append(mean + 0.5 * s)
        if mean + 3 * s < 1:
            thresholds.append(mean + 3 * s)
        thresholds.append(1)
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
                if s['grade'] < t:
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

        labels = [_('to ') + str(i['max_progress']) + ' %' for i in cohorts]
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


class InstructorAnalyticsFragmentView(AccessMixin, FragmentView):
    """
    Fragment for render tab.
    """

    def process(self, request, **kwargs):
        """
        Render tab fragment.
        """
        course = kwargs['course']

        enroll_start = course.enrollment_start
        if enroll_start is None:
            enroll_start = course.start

        enroll_end = course.enrollment_end
        if enroll_end is None:
            enroll_end = course.end

        enroll_info = {
            'enroll_start': mktime(enroll_start.timetuple()) if enroll_start else 'null',
            'enroll_end': mktime(enroll_end.timetuple()) if enroll_end else 'null',
        }
        context = {
            'course': course,
            'enroll_info': enroll_info
        }

        log.debug(context)
        html = render_to_string('rg_instructor_analytics/instructor_analytics_fragment.html', context)
        fragment = Fragment(html)
        fragment.add_javascript_url(JS_URL + 'instructor_analytics.js')
        fragment.add_css_url(CSS_URL + 'instructor_analytics.css')

        return fragment
