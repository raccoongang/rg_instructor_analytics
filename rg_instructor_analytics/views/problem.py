"""
Module for problem subtab.
"""
from abc import ABCMeta, abstractmethod
from itertools import chain
import json

from django.db.models import Avg, IntegerField, Sum
from django.db.models.expressions import RawSQL
from django.http.response import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View
from opaque_keys.edx.keys import CourseKey

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from courseware.module_render import xblock_view
from rg_instructor_analytics.utils.AccessMixin import AccessMixin
from rg_instructor_analytics.utils.decorators import instructor_access_required

QUESTUIN_SELECT_TYPE = 'select'
QUESTUIN_MULTI_SELECT_TYPE = 'multySelect'


class ProblemHomeWorkStatisticView(View):
    """
    Homework problem stats API view for given course.
    """

    ATTEMPTS_REQUEST = RawSQL(
        "SELECT SUBSTRING_INDEX(SUBSTRING_INDEX(state,'attempts\": ',-1),',',1)",
        (),
        output_field=IntegerField()
    )

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(ProblemHomeWorkStatisticView, self).dispatch(*args, **kwargs)

    def post(self, request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        stats_course_id = request.POST.get('course_id')
        return JsonResponse(data=self.get_homework_stat(stats_course_id))

    def academic_performance_request(self, course_key):
        """
        Make request to db for academic performance.

        Return list, where each item contain id of the problem, average count of attempts and percent of correct answer.
        """
        return (
            StudentModule.objects
            .filter(course_id__exact=course_key, grade__isnull=False, module_type__exact="problem")
            .values('module_state_key')
            .annotate(attempts_avg=Avg(self.ATTEMPTS_REQUEST))
            .annotate(grade_avg=Sum('grade') / Sum('max_grade'))
            .values('module_state_key', 'attempts_avg', 'grade_avg')
        )

    def get_academic_performance(self, course_key):
        """
        Provide map, where key - course and value - map with average grade and attempt.
        """
        return {
            i['module_state_key']: {'grade_avg': i['grade_avg'], 'attempts_avg': i['attempts_avg']}
            for i in self.academic_performance_request(course_key)
        }

    def get_homework_stat(self, course_id):
        """
        Provide statistic for given course.

        :param course_key:  object, that represent course.
        :return: map with list of correct answers, attempts, list of the problems for unit and names.
        Each item of given list represent one unit.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_by_id(course_key, depth=4)

        academic_performance = self.get_academic_performance(course_key)

        def process_stats():
            """
            Process students module data.

            NOTE(wowkalucky): optimize - currently 'process_stats' takes about 11033.25 ms
            """
            stats = {
                'correct_answer': [], 'attempts': [], 'problems': [], 'names': [], 'subsection_id': []
            }
            hw_number = 0

            course_children = course.get_children()
            for subsection in chain.from_iterable(section.get_children() for section in course_children):
                if not subsection.graded:
                    continue
                hw_number += 1
                stats['correct_answer'].append(0)
                stats['attempts'].append(0)
                stats['problems'].append([])
                stats['names'].append(subsection.display_name)
                stats['subsection_id'].append(subsection.location.to_deprecated_string())

                problems_in_hw = 0

                for child in chain.from_iterable(unit.get_children() for unit in subsection.get_children()):
                    if child.location.category == 'problem':
                        problem_id = child.location.to_deprecated_string()
                        if problem_id in academic_performance:
                            current_performance = academic_performance[problem_id]
                            stats['correct_answer'][-1] += current_performance['grade_avg']
                            stats['attempts'][-1] += current_performance['attempts_avg']
                            problems_in_hw += 1

                        stats['problems'][-1].append(problem_id)

                if problems_in_hw > 0:
                    stats['correct_answer'][-1] /= problems_in_hw
                    stats['attempts'][-1] /= problems_in_hw
            return stats

        return process_stats()


class ProblemsStatisticView(AccessMixin, View):
    """
    Api for getting statistic for each problem in unit.
    """

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        course_key = kwargs['course_key']
        problems_ids = request.POST.getlist('problems')
        problems = [course_key.make_usage_key_from_deprecated_string(p) for p in problems_ids]
        stats = (
            StudentModule.objects
            .filter(module_state_key__in=problems, grade__isnull=False)
            .values('module_state_key')
            .annotate(grades=Sum('grade'))
            .annotate(max_grades=Sum('max_grade'))
            .annotate(attempts=Avg(ProblemHomeWorkStatisticView.ATTEMPTS_REQUEST))
            .values('module_state_key', 'grades', 'max_grades', 'attempts')
        )

        problems_stat = [None] * len(problems_ids)
        for s in stats:
            problems_stat[problems_ids.index(s['module_state_key'])] = s

        def record(stat_item):
            if not stat_item or not stat_item['attempts']:
                return 0, 0
            correct = int((float(stat_item['grades']) / float(stat_item['max_grades'] * stat_item['attempts'])) * 100)
            incorrect = 100 - correct
            return incorrect, correct

        incorrect, correct = tuple(map(list, zip(*[record(s) for s in problems_stat]))) or ([], [])

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


class ProblemQuestionParser():
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
        """
        Process post request.
        """
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
