"""
Module for problem subtab.
"""
from abc import ABCMeta, abstractmethod
from itertools import chain
import json

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from courseware.module_render import xblock_view
from django.db.models import Avg, Sum
from django.db.models import IntegerField
from django.db.models.expressions import RawSQL
from django.http.response import JsonResponse
from django.views.generic import View

from rg_instructor_analytics.utils.AccessMixin import AccessMixin


def info_for_course_element(element, level):
    return {
        'level': level,
        'name': element.display_name,
        'id': element.location.to_deprecated_string(),
        'children': []
    }


def add_as_child(element, child):
    element['children'].append(child)

class GradeFunnelView(AccessMixin, View):
    """
    Api for get homework`s statistic for given course.
    """

    def get_progress_info(self,course_key):
        StudentModule.objects
        .filter(course_id__exact=course_key, grade__isnull=False, module_type__exact="problem")
        .values('module_state_key')
        .annotate(attempts_avg=Avg(attempts))
        .annotate(grade_avg=Sum('grade') / Sum('max_grade'))
        .values('module_state_key', 'attempts_avg', 'grade_avg')

    def get_course_info(self,course_key):
        course_info = []
        course = get_course_by_id(course_key, depth=4)
        for section in course.get_children():
            section_info = info_for_course_element(section, level=0)
            for subsection in section.get_children():
                subsection_info = info_for_course_element(subsection, level=1)
                for unit in subsection.get_children():
                    unit_info = info_for_course_element(unit, level=2)
                    for child in unit.get_children():
                        if child.location.category == 'problem':
                            add_as_child(unit_info, info_for_course_element(child, level=3))
                    add_as_child(subsection_info, unit_info)
                add_as_child(section_info, subsection_info)
            course_info.append(section_info)
        return course_info

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        course_key = kwargs['course_key']
        self.get_course_info(course_key)
        import ipdb;ipdb.set_trace(context=12)
        return JsonResponse(data={'status':'ok'})
