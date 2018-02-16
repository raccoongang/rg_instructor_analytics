"""
Module for problem subtab.
"""
from abc import ABCMeta, abstractmethod
from itertools import chain
import json

from django.db.models import Avg, Sum
from django.db.models import IntegerField
from django.db.models.expressions import RawSQL
from django.http.response import JsonResponse
from django.views.generic import View

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from courseware.module_render import xblock_view
from rg_instructor_analytics.utils.AccessMixin import AccessMixin


QUESTUIN_SELECT_TYPE = 'select'
QUESTUIN_MULTI_SELECT_TYPE = 'multySelect'


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

        Return list, where each item contain id of the problem, average count of attempts and percent of correct answer.
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
        :return: map with list of correct answers, attempts, list of the problems for unit and names.
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
