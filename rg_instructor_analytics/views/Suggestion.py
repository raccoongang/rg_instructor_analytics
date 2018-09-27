"""
Module for the suggestion's tab logic.
"""
from abc import ABCMeta, abstractmethod
from itertools import izip

from django.views.generic import View
import numpy as np

from course_modes.models import CourseMode
from django_comment_client.utils import JsonResponse
from rg_instructor_analytics.utils.AccessMixin import AccessMixin
from rg_instructor_analytics.views.Funnel import GradeFunnelView
from rg_instructor_analytics.views.Problem import ProblemHomeWorkStatisticView


class BaseSuggestion(object):
    """
    Base class for the suggestion generator.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        """
        Construct suggestion.
        """
        super(BaseSuggestion, self).__init__()
        self.suggestion = []

    @abstractmethod
    def suggestion_source(self, item_id):
        """
        Return Linked list structure, where head contains tab name and tail point to some position of the tab.

        I.E.:
            {
                'value': 'parent',
                'child': {
                    'value': child_id
                }
            }
        """
        pass

    def add_suggestion_item(self, description, item_id):
        """
        Add new suggestion item in to suggestion list.

        :param description: description, that shown to a user.
        :param item_id: id of the course item.
        """
        self.suggestion.append({
            'description': description,
            'location': self.suggestion_source(item_id),
        })

    def get_suggestion_list(self, course_key, cohort):
        """
        Return suggestion list.

        Generate new suggestion list and return it.
        Also, new list will stored inside suggestion field of the current instance.
        """
        self.suggestion = []
        self.generate_suggestion(course_key, cohort)
        return self.suggestion

    @abstractmethod
    def generate_suggestion(self, course_key, cohort):
        """
        Use for generate suggestion for the course.

        Abstract method with custom logic for generating new suggestion list.
        For adding new suggestion item used function  `add_suggestion_item`.
        """
        pass


class FunnelSuggestion(BaseSuggestion):
    """
    Suggestion generator, based on the funnel tab.
    """

    def suggestion_source(self, item_id):
        """
        Implement parent method.
        """
        return {
            'value': 'funnel',
            'child': {
                'value': item_id,
            }
        }

    def filter_funnel(self, funnel):
        """
        Filter funnel with level equal 2 and with non zero student on the section.
        """
        result = []
        for item in funnel:
            if item['level'] == 1 and item['student_count_in'] > 0:
                result.append(item)
            if item.get('children'):
                result += self.filter_funnel(item['children'])
        return result

    def generate_suggestion(self, course_key, cohort):
        """
        Generate suggestion, based on the funnels tab information.
        """
        funnel = GradeFunnelView()
        funnel.user_enrollments_ignored_types = [CourseMode.AUDIT]
        units = list(self.filter_funnel(funnel.get_funnel_info(course_key, cohort)))

        def get_percent(total, put):
            return .0 if not (total and put) else float(put) / float(total)

        subsections_percent = np.array([get_percent(unit['student_count_in'], unit['student_count']) for unit in units])
        # Get an array of elements, which are satisfied to the condition in the brackets. (numpy's feature)
        subsections_percent = subsections_percent[subsections_percent < 1.0]

        threshold = subsections_percent.mean() + subsections_percent.std()

        description = 'Take a look at `{}`: the number of students that stuck there is {}% higher than average'
        for unit in units:
            percent = get_percent(unit['student_count_in'], unit['student_count'])
            if unit['student_count_in'] > 0 and threshold <= percent < 1.0:
                self.add_suggestion_item(description.format(unit['name'], int(percent * 100.0)), unit['id'])


class ProblemSuggestion(BaseSuggestion):
    """
    Suggestion generator, based on the problem tab.
    """

    def suggestion_source(self, item_id):
        """
        Implement parent method.
        """
        return {
            'value': 'problems',
            'child': {
                'value': item_id,
            }

        }

    def generate_suggestion(self, course_key, cohort):
        """
        Generate suggestion, based on the funnels tab information.
        """
        problem_stat = ProblemHomeWorkStatisticView().get_homework_stat(course_key, cohort)
        problem_stat['success'] = map(
            lambda (grade, attempts): attempts and grade / attempts,
            izip(problem_stat['correct_answer'], problem_stat['attempts'])
        )

        problems = np.array(problem_stat['success'])
        problems = problems[np.nonzero(problems)]
        threshold = problems.mean() - problems.std()

        description = (
            'Take a look at `{}`: there is too high avg attempts number and too low value of the mean success rate'
        )
        for i in range(len(problem_stat['success'])):
            if problem_stat['success'][i] and problem_stat['success'][i] < threshold:
                self.add_suggestion_item(
                    description.format(problem_stat['names'][i]),
                    problem_stat['subsection_id'][i],
                )


class SuggestionView(AccessMixin, View):
    """
    Api for get courses suggestion.
    """

    suggestion_providers = [
        FunnelSuggestion(),
        ProblemSuggestion(),
    ]

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        result = sum([s.get_suggestion_list(kwargs['course_key'], kwargs['cohort']) for s in self.suggestion_providers], [])
        return JsonResponse(data={'suggestion': result})
