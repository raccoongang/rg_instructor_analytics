"""
Module for the suggestion's tab logic.
"""
from itertools import chain

from abc import ABCMeta, abstractmethod
from django.db.models import Sum, Count
from django.db.models.expressions import RawSQL
from django.forms import IntegerField
from django.views.generic import View
from opaque_keys.edx.keys import UsageKey

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from django_comment_client.utils import JsonResponse
from rg_instructor_analytics.utils.AccessMixin import AccessMixin
from rg_instructor_analytics.views.Funnel import GradeFunnelView


class BaseSuggestion(object):

    __metaclass__ = ABCMeta

    def __init__(self):
        super(BaseSuggestion, self).__init__()
        self.suggestion = []

    def add_suggestion_item(self, description, item_id):
        self.suggestion.append({
            'description': description,
            'item_id': item_id
        })

    def get_suggestion_list(self, course_key):
        self.suggestion = []
        self.generate_suggestion(course_key)
        return self.suggestion

    @abstractmethod
    def generate_suggestion(self, course_key):
        pass


class FunnelSuggestion(BaseSuggestion):
    stuck_threshold = 25

    def filter_funnel(self, funnel, conditions):
        result = []
        for i in funnel:
            if conditions(i):
                result.append(i)
            if i.get('children'):
                result += self.filter_funnel(i['children'], conditions)
        return result

    def generate_suggestion(self, course_key):
        units = list(self.filter_funnel(GradeFunnelView().get_funnel_info(course_key),lambda item: item['level'] == 2))

        def get_percent(total, put):
            return 0 if not (total and put) else float(put) / float(total)

        total_stuck_percent, count = 0, 0
        for unit in units:
            if unit['student_count_in'] > 0:
                total_stuck_percent += get_percent(unit['student_count'], unit['student_count_in'])
                count += 1
        stuck_percent = total_stuck_percent/count

        description = 'Take a look at `{}`: the number of students that stuck there is {}% higher than average'
        for unit in units:
            percent = get_percent(unit['student_count_in'], unit['student_count'])
            if unit['student_count_in'] > 0 and percent >= stuck_percent:
                self.add_suggestion_item(description.format(unit['name'], int(percent*100.0)), unit['id'])


class ProblemSuggestion(BaseSuggestion):

    def get_prblem_by_unit(self,course_key):
        course = get_course_by_id(course_key, depth=4)
        problems_by_unit = {}
        for subsection in chain.from_iterable(section.get_children() for section in course.get_children()):
            for unit in subsection.get_children():
                problems = [
                    child.location.to_deprecated_string()
                    for child in unit.get_children() if child.location.category == 'problem'
                ]
                if len(problems):
                    problems_by_unit[unit.location.to_deprecated_string()] = {
                        'problems': problems,
                        'name': unit.display_name,
                        'is_graded':subsection.graded,
                    }
        return problems_by_unit

    def get_all_problems_id(self, problems_per_unit):
        return [
            UsageKey.from_string(problem)
            for problem in sum([v['problems'] for k, v in problems_per_unit.iteritems()], [])
        ]

    def get_problems_stat(self, course_key, problem_list):
        if not len(problem_list):
            return []
        attempts = RawSQL("SELECT SUBSTRING_INDEX(SUBSTRING_INDEX(state,'attempts\": ',-1),',',1)", ())
        return (StudentModule.objects
                .filter(course_id__exact=course_key,
                        grade__isnull=False,
                        module_type__exact="problem",
                        module_state_key__in=problem_list
                        )
                .values('module_state_key')
                .annotate(attempts=Sum(attempts))
                .annotate(grades=Sum('grade'))
                .annotate(max_grades=Sum('max_grade'))
                .annotate(record_count=Count('module_state_key'))
                .values('module_state_key', 'attempts', 'grades', 'max_grades','record_count'))


    def update_unit_info_from_problems_list(self,units_map,problems_list):
        tem_unit_info = {}
        for p in problems_list:
            for unit_key,unit_info in units_map.iteritems():
                if p['module_state_key'] in unit_info['problems']:
                    if unit_key not in tem_unit_info:
                        tem_unit_info[unit_key] = {
                            'count': 0,
                            'grade': 0,
                            'attempts': 0,
                        }
                    tem_unit_info[unit_key]['attempts'] += p['attempts']
                    tem_unit_info[unit_key]['grade'] += (p['grades']/p['max_grades'])*p['record_count']
                    tem_unit_info[unit_key]['count'] += p['record_count']

        import ipdb;ipdb.set_trace()
        for unit_key, unit_info in units_map.iteritems():
            if unit_key in tem_unit_info:
                info = tem_unit_info[unit_key]
                a = (info['attempts'] / info['count']) ** (-1)
                g = info['grade'] / info['count']
                unit_info['success'] = 2 * ((a * g) / (a + g))
            else:
                unit_info['success'] = 0
        return units_map

    def generate_suggestion(self, course_key):
        problems_by_unit = self.get_prblem_by_unit(course_key)
        problems_info = self.get_problems_stat(course_key, self.get_all_problems_id(problems_by_unit))
        self.update_unit_info_from_problems_list(problems_by_unit,problems_info)
        import ipdb;ipdb.set_trace()
        pass


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
        result = sum([s.get_suggestion_list(kwargs['course_key']) for s in self.suggestion_providers],[])
        return JsonResponse(data={'suggestion':result})
