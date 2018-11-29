"""
Problems sub-tab module.
"""
from abc import ABCMeta, abstractmethod
from datetime import date, timedelta
from itertools import chain
import json

from django.db.models import Avg, IntegerField, Q, Sum
from django.db.models.expressions import RawSQL
from django.http.response import HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from courseware.module_render import xblock_view
from rg_instructor_analytics.utils.decorators import instructor_access_required

QUESTION_SELECT_TYPE = 'select'
QUESTION_MULTI_SELECT_TYPE = 'multySelect'


class ProblemHomeWorkStatisticView(View):
    """
    Homework problem stats API view for given course.

    Data source: StudentModule DB model + Course structure.
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
        post_data = request.POST
        stats_course_id = post_data.get('course_id')

        try:
            from_date = post_data.get('from') and date.fromtimestamp(float(post_data['from']))
            to_date = post_data.get('to') and date.fromtimestamp(float(post_data['to']))

            course_key = CourseKey.from_string(stats_course_id)
        except ValueError:
            return HttpResponseBadRequest(_("Invalid date range."))
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        return JsonResponse(
            data=self.get_homework_stat(course_key, from_date, to_date)
        )

    def get_homework_stat(self, course_key, from_date=None, to_date=None):
        """
        Aggregate students' attemps/grade info for given course.

        :param course_key:  Edx CourseKey object.
        :param from_date:  (Date) stats period start.
        :param to_date:  (Date) stats period end.
        :return: map with list of correct answers, attempts, list of the problems for unit and names.
        Each item of given list represent one unit.
        """
        academic_performance = {
            i['module_state_key']: {'grade_avg': i['grade_avg'], 'attempts_avg': i['attempts_avg']}
            for i in self.academic_performance_request(course_key, from_date, to_date)
        }

        def process_stats():
            """
            Process students module data.

            NOTE(wowkalucky): optimize - currently 'process_stats' takes about 11 sec!
            """
            stats = {
                'correct_answer': [], 'attempts': [], 'problems': [], 'names': [], 'subsection_id': []
            }
            hw_number = 0

            course = get_course_by_id(course_key, depth=4)
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

    def academic_performance_request(self, course_key, from_date, to_date):
        """
        Academic performance DB request.

        Forms list, where each item contains:
        - problem id,
        - average count of attempts,
        - correct answers percent (only last grades are taken into account...)
        """
        date_range_filter = Q(modified__range=(
            from_date, to_date + timedelta(days=1))
        ) if from_date and to_date else Q()

        return (
            StudentModule.objects
            .filter(
                date_range_filter,
                course_id__exact=course_key,
                grade__isnull=False,
                module_type__exact="problem",
            )
            .values('module_state_key')
            .annotate(attempts_avg=Avg(self.ATTEMPTS_REQUEST))
            .annotate(grade_avg=Sum('grade') / Sum('max_grade'))
            .values('module_state_key', 'attempts_avg', 'grade_avg')
        )


class ProblemsStatisticView(View):
    """
    Certain problem's stats in Unit.

    Data source: StudentModule DB model.
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(ProblemsStatisticView, self).dispatch(*args, **kwargs)

    def post(self, request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        post_data = request.POST
        stats_course_id = post_data.get('course_id')

        try:
            from_date = post_data.get('from') and date.fromtimestamp(float(post_data['from']))
            to_date = post_data.get('to') and date.fromtimestamp(float(post_data['to']))

            course_key = CourseKey.from_string(stats_course_id)
        except ValueError:
            return HttpResponseBadRequest(_("Invalid date range."))
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        problems_ids = post_data.getlist('problems')
        problems = [course_key.make_usage_key_from_deprecated_string(p) for p in problems_ids]

        date_range_filter = Q(modified__range=(
            from_date, to_date + timedelta(days=1))
        ) if from_date and to_date else Q()

        stats = (
            StudentModule.objects
            .filter(
                date_range_filter,
                module_state_key__in=problems,
                grade__isnull=False
            )
            .values('module_state_key')
            .annotate(grades=Sum('grade'))
            .annotate(max_grades=Sum('max_grade'))
            .annotate(attempts=Avg(ProblemHomeWorkStatisticView.ATTEMPTS_REQUEST))
            .values('module_state_key', 'grades', 'max_grades', 'attempts')
        )

        students_emails = list(StudentModule.objects.filter(
            date_range_filter,
            module_state_key__in=problems,
            grade__isnull=False
        ).values_list('student__email', flat=True).distinct())

        problems_stat = [None] * len(problems_ids)
        for s in stats:
            problems_stat[problems_ids.index(s['module_state_key'])] = s

        def record(stat_item):
            if not stat_item or not stat_item['attempts']:
                return 0, 0
            correct = int(
                (float(stat_item['grades']) / float(stat_item['max_grades'] * stat_item['attempts'])) * 100
            )
            incorrect = 100 - correct
            return incorrect, correct

        incorrect, correct = tuple(map(list, zip(*[record(s) for s in problems_stat]))) or ([], [])

        return JsonResponse(data={'incorrect': incorrect, 'correct': correct, 'students_emails': students_emails})


class ProblemDetailView(View):
    """
    Problem detail API view.
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(ProblemDetailView, self).dispatch(*args, **kwargs)

    def post(self, request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        return xblock_view(request, request.POST.get('course_id'), request.POST['problem'], 'student_view')


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


class ProblemQuestionView(View):
    """
    Api for question statistic.
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(ProblemQuestionView, self).dispatch(*args, **kwargs)

    def post(self, request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        post_data = request.POST
        stats_course_id = post_data.get('course_id')

        try:
            q_type = post_data.get('type')
            question_id = post_data.get('questionID')
            problem_id = post_data.get('problemID')

            answer_map = json.loads(post_data.get('answerMap'))

            course_key = CourseKey.from_string(stats_course_id)
            problem_usage_key = course_key.make_usage_key_from_deprecated_string(problem_id)
        except ValueError:
            return HttpResponseBadRequest(_("Invalid `answerMap` (JSON parsing error)."))
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        if q_type == QUESTION_SELECT_TYPE:
            result = ProblemSelectQuestion(problem_usage_key, question_id, answer_map).get_statistic()
        elif q_type == QUESTION_MULTI_SELECT_TYPE:
            result = ProblemMultiSelectQuestion(problem_usage_key, question_id, answer_map).get_statistic()
        else:
            result = {}

        return JsonResponse(data=result)


class ProblemStudentDataView(View):
    """
    Problem student data API view.
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(ProblemStudentDataView, self).dispatch(*args, **kwargs)

    def post(self, request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        post_data = request.POST
        course_id = post_data.get('course_id')
        problem = post_data.get('problem')

        try:
            from_date = post_data.get('from') and date.fromtimestamp(float(post_data['from']))
            to_date = post_data.get('to') and date.fromtimestamp(float(post_data['to']))
            course_key = CourseKey.from_string(course_id)
        except ValueError:
            return HttpResponseBadRequest(_("Invalid date range."))
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        problem_key = course_key.make_usage_key_from_deprecated_string(problem)

        date_range_filter = Q(modified__range=(
            from_date, to_date + timedelta(days=1))
        ) if from_date and to_date else Q()

        students_emails = list(StudentModule.objects.filter(
            date_range_filter,
            module_state_key=problem_key,
            grade__isnull=False
        ).values_list('student__email', flat=True).distinct())

        return JsonResponse(data={'students_emails': students_emails})
