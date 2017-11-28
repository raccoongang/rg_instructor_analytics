"""
Module for tab fragment and api views.
"""
from abc import ABCMeta, abstractmethod
from datetime import datetime
from itertools import chain
import json
import logging
from time import mktime

from courseware.access import has_access
from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from courseware.module_render import xblock_view
from django.conf import settings
from django.db.models import Avg, Count, Q, Sum
from django.db.models import IntegerField
from django.db.models.expressions import RawSQL
from django.db.models.fields import DateField
from django.http import HttpResponseBadRequest
from django.http.response import HttpResponseForbidden, JsonResponse
from django.views.generic import View
from edxmako.shortcuts import render_to_string
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from student.models import CourseEnrollment
from web_fragments.fragment import Fragment

logging.basicConfig()

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

JS_URL = '{static_url}rg_instructor_analytics/js/'.format(static_url=settings.STATIC_URL)
CSS_URL = '{static_url}rg_instructor_analytics/css/'.format(static_url=settings.STATIC_URL)

QUESTUIN_SELECT_TYPE = 'select'
QUESTUIN_MULTI_SELECT_TYPE = 'multySelect'


class EnrollmentStatisticView(View):
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

    def post(self, request, course_id):
        """
        Process post request for this view.
        """
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error("Unable to find course with course key %s while getting enrollment statistic", course_id)
            return HttpResponseBadRequest()
        course = get_course_by_id(course_key, depth=0)
        if not has_access(request.user, 'staff', course):
            log.error("Enrollment statistics not available for user type `%s`", request.user)
            return HttpResponseForbidden()

        from_timestamp = int(request.POST['from'])
        to_timestamp = int(request.POST['to'])

        return JsonResponse(data=self.get_statistic_per_day(from_timestamp, to_timestamp, course_key))


class ProblemHomeWorkStatisticView(View):
    """Api for get homework`s statistic for given course."""

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

        return (StudentModule.objects
                             .filter(course_id__exact=course_key, grade__isnull=False, module_type__exact="problem")
                             .values('module_state_key')
                             .annotate(attempts_avg=Avg(attempts))
                             .annotate(grade_avg=Sum('grade') / Sum('max_grade'))
                             .values('module_state_key', 'attempts_avg', 'grade_avg'))

    @classmethod
    def get_academic_performance(cls, course_key):
        """Provide map, where key - course and value - map with average grade and attempt."""
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

    def post(self, request, course_id):
        """Process post request."""
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error(u"Unable to find course with course key %s while getting enrollment statistic", course_id)
            return HttpResponseBadRequest()

        if not has_access(request.user, 'staff', course_key):
            log.error("Problem homework statistics not available for user type `%s`", request.user)
            return HttpResponseForbidden()

        stat = self.get_homework_stat(course_key)

        return JsonResponse(data=stat)


class ProblemsStatisticView(View):
    """Api for getting statistic for each problem in unit."""

    def post(self, request, course_id):
        """Process post request."""
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error(u"Unable to find course with course key %s while getting enrollment statistic", course_id)
            return HttpResponseBadRequest()

        if not has_access(request.user, 'staff', course_key):
            log.error("Problem`s statistics not available for user type `%s`", request.user)
            return HttpResponseForbidden()

        problems = [course_key.make_usage_key_from_deprecated_string(p) for p in request.POST.getlist('problems')]
        stats = (StudentModule.objects
                              .filter(module_state_key__in=problems)
                              .values('module_state_key')
                              .annotate(correct=Sum('grade'))
                              .annotate(incorrect=Sum('grade') - Sum('max_grade'))
                              .values('module_state_key', 'correct', 'incorrect'))
        incorrect, correct = tuple(map(list, zip(*[(int(s['incorrect'] or 0), int(s['correct'] or 0)) for s in stats])))
        return JsonResponse(data={'incorrect': incorrect, 'correct': correct})


class ProblemDetailView(View):
    """Api for getting problem detail."""

    def post(self, request, course_id):
        """Process post request."""
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error(u"Unable to find course with course key %s while getting enrollment statistic", course_id)
            return HttpResponseBadRequest()

        if not has_access(request.user, 'staff', course_key):
            log.error("Problem detail not available for user type `%s`", request.user)
            return HttpResponseForbidden()

        result = xblock_view(request, course_id, request.POST['problem'], 'student_view')
        return result


class ProblemQuestionParser:
    """Base class for provide statistic for question."""

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
        """Provide init state for statistic."""
        return {}

    @abstractmethod
    def process_statistic_item(self, state, item):
        """Abstract method for process data form database and update statistic."""
        pass

    def get_statistic(self):
        """Provide statistic for given question."""
        problems = StudentModule.objects.filter(module_state_key=self.problemID, grade__isnull=False,
                                                module_type__exact="problem").values_list('state', flat=True)
        result = self.init_statistic_object()
        for p in problems:
            self.process_statistic_item(result, json.loads(p))
        return result


class ProblemSelectQuestion(ProblemQuestionParser):
    """Class for process question with `select` type (dropdown and single choice)."""

    def __init__(self, problemID, questionID, answer_map):
        """Implement constructor."""
        super(ProblemSelectQuestion, self).__init__(problemID, questionID, answer_map)

    def init_statistic_object(self):
        """Overwrite base class."""
        return {'type': 'bar', 'stats': {v: 0 for v in self.answer_map.values()}}

    def process_statistic_item(self, state, item):
        """Overwrite base class."""
        state['stats'][self.answer_map[item['student_answers'][self.questionID]]] += 1


class ProblemMultiSelectQuestion(ProblemSelectQuestion):
    """Class for process question with `multySelect` type (question with checkboxes)."""

    def __init__(self, problemID, questionID, answer_map):
        """Implement constructor."""
        super(ProblemMultiSelectQuestion, self).__init__(problemID, questionID, answer_map)

    def process_statistic_item(self, state, item):
        """Overwrite base class."""
        for answer in item['student_answers'][self.questionID]:
            state['stats'][self.answer_map[answer]] += 1


class ProblemQuestionView(View):
    """Api for question statistic."""

    def post(self, request, course_id):
        """Process post request."""
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error(u"Unable to find course with course key %s while getting enrollment statistic", course_id)
            return HttpResponseBadRequest()

        if not has_access(request.user, 'staff', course_key):
            log.error("Question statistic not available for user type `%s`", request.user)
            return HttpResponseForbidden()

        type = request.POST['type']
        questionID = request.POST['questionID']
        answer_map = json.loads(request.POST['answerMap'])
        problemID = course_key.make_usage_key_from_deprecated_string(request.POST['problemID'])

        if type == QUESTUIN_SELECT_TYPE:
            result = ProblemSelectQuestion(problemID, questionID, answer_map).get_statistic()
        elif type == QUESTUIN_MULTI_SELECT_TYPE:
            result = ProblemMultiSelectQuestion(problemID, questionID, answer_map).get_statistic()
        else:
            result = {}

        return JsonResponse(data=result)


class InstructorAnalyticsFragmentView(EdxFragmentView):
    """
    Fragment for render tab.
    """

    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Render tab fragment.
        """
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error("Unable to find course with course key %s while loading the Instructor Analytics Dashboard.",
                      course_id)
            return HttpResponseBadRequest()

        course = get_course_by_id(course_key, depth=0)
        if not has_access(request.user, 'staff', course):
            log.error("Statistics not available for user type `%s`", request.user)
            return HttpResponseForbidden()

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
