"""
Suggestions tab module.
"""
from abc import ABCMeta, abstractmethod
from itertools import izip

from django.http import HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
import numpy as np
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from course_modes.models import CourseMode
from django_comment_client.utils import JsonResponse
from rg_instructor_analytics.utils.decorators import instructor_access_required
from rg_instructor_analytics.views.funnel import GradeFunnelView
from rg_instructor_analytics.views.problem import ProblemHomeWorkStatisticView


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

    def get_suggestion_list(self, course_key, cohort_id):
        """
        Return suggestion list.

        Generate new suggestion list and return it.
        Also, new list will stored inside suggestion field of the current instance.
        """
        self.suggestion = []
        self.generate_suggestion(course_key, cohort_id)
        return self.suggestion

    @abstractmethod
    def generate_suggestion(self, course_key, cohort_id):
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

    def generate_suggestion(self, course_key, cohort_id):
        """
        Generate suggestion, based on the funnels tab information.
        """
        funnel = GradeFunnelView()
        funnel.user_enrollments_ignored_types = [CourseMode.AUDIT]
        units = list(self.filter_funnel(funnel.get_funnel_info(course_key, cohort_id)))

        def get_percent(total, put):
            return .0 if not (total and put) else float(put) / float(total)

        subsections_percent = np.array([get_percent(unit['student_count_in'], unit['student_count']) for unit in units])
        # Get an array of elements, which are satisfied to the condition in the brackets. (numpy's feature)
        subsections_percent = subsections_percent[subsections_percent < 1.0]

        threshold = subsections_percent.mean() + subsections_percent.std()

        description = 'Take a look at "{}" - ' \
                      'the number of students that stuck there is {:01.0f}% higher than average.'

        for unit in units:
            percent = get_percent(unit['student_count_in'], unit['student_count'])
            if unit['student_count_in'] > 0 and threshold <= percent < 1.0:
                self.add_suggestion_item(description.format(
                    '<b>{}</b>'.format(unit['name']),
                    percent * 100.0),
                    unit['id']
                )


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

    def generate_suggestion(self, course_key, cohort_id):
        """
        Generate suggestion, based on the funnels tab information.
        """
        problem_stat = ProblemHomeWorkStatisticView().get_homework_stat(course_key, cohort_id)
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


class SuggestionView(View):
    """
    Courses suggestions API view.
    """

    suggestion_providers = [
        FunnelSuggestion(),
        ProblemSuggestion(),
    ]

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(SuggestionView, self).dispatch(*args, **kwargs)

    def post(self, request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        try:
            cohort_id = request.POST.get('cohort_id')
            stats_course_id = request.POST.get('course_id')
            course_key = CourseKey.from_string(stats_course_id)

        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        result = sum([s.get_suggestion_list(course_key, cohort_id) for s in self.suggestion_providers], [])
        return JsonResponse(data={'suggestion': result})
