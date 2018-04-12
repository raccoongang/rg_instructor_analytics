"""
Module for funnel subtab.
"""
import json

from django.db.models import Count
from django.db.models.expressions import RawSQL
from django.http.response import JsonResponse
from django.views.generic import View

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from rg_instructor_analytics.utils.AccessMixin import AccessMixin


def info_for_course_element(element, level):
    """
    Return new element of the course item.
    """
    return {
        'level': level,
        'name': element.display_name,
        'id': element.location.to_deprecated_string(),
        'student_count': 0,
        'student_count_in': 0,
        'student_count_out': 0,
        'children': [],
    }


def add_as_child(element, child):
    """
    Append to dictionary new element, named children.
    """
    element['children'].append(child)


class GradeFunnelView(AccessMixin, View):
    """
    Api for get funnel for given course.
    """

    def get_query_for_course_item_stat(self, course_key, block_type):
        """
        Return query set for select given block type for given course.
        """
        return (
            StudentModule.objects.filter(
                course_id=course_key,
                module_type=block_type,
                modified__exact=RawSQL(
                    "(SELECT MAX(t2.modified) FROM courseware_studentmodule t2 " +
                    "WHERE (t2.student_id = courseware_studentmodule.student_id) AND t2.course_id = %s "
                    "AND t2.module_type = %s)", (course_key, block_type))
            )
        )

    def get_progress_info_for_subsection(self, course_key):
        """
        Return activity for each of the section.
        """
        info = self.get_query_for_course_item_stat(course_key, 'sequential')
        info = (
            info.values('module_state_key', 'state')
                .order_by('module_state_key', 'state')
                .annotate(count=Count('module_state_key'))
                .values('module_state_key', 'state', 'count')
        )

        result = {}
        for i in info:
            if i['module_state_key'] not in result:
                result[i['module_state_key']] = []
            result[i['module_state_key']].append({
                'count': i['count'],
                'offset': json.loads(i['state'])['position']
            })

        return result

    def get_course_info(self, course_key, subsection_activity):
        """
        Return information about the course in tree view.
        """
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
                if subsection_info['id'] in subsection_activity:
                    for u in subsection_activity[subsection_info['id']]:
                        subsection_info['children'][u['offset'] - 1]['student_count'] = u['count']
                        subsection_info['student_count'] += u['count']
                    section_info['student_count'] += subsection_info['student_count']
            course_info.append(section_info)
        return course_info

    def append_inout_info(self, statistic, accomulate=0):
        """
        Append information about how many student in course.
        """
        for i in reversed(statistic):
            i['student_count_out'] = accomulate
            if len(i['children']):
                self.append_inout_info(i['children'], accomulate=accomulate)
            accomulate += i['student_count']
            i['student_count_in'] = accomulate

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        course_key = kwargs['course_key']
        subsection_activity = self.get_progress_info_for_subsection(course_key)
        courses_structure = self.get_course_info(course_key, subsection_activity)
        self.append_inout_info(courses_structure)
        return JsonResponse(data={'courses_structure': courses_structure})
