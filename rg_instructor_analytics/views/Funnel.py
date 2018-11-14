"""
Module for funnel subtab.
"""
import json
import logging

from django.db.models import Count
from django.db.models.expressions import RawSQL
from django.http.response import JsonResponse
from django.views.generic import View

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from rg_instructor_analytics.utils.AccessMixin import AccessMixin
from student.models import CourseEnrollment

log = logging.getLogger(__name__)


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

    user_enrollments_ignored_types = []

    def get_query_for_course_item_stat(self, course_key, block_type, cohort):
        """
        Return query set for select given block type for given course.
        """
        # TODO use preaggregation
        modified_filter = RawSQL(
            "(SELECT MAX(t2.modified) FROM courseware_studentmodule t2 " +
            "WHERE (t2.student_id = courseware_studentmodule.student_id) AND t2.course_id = %s "
            "AND t2.module_type = %s)", (course_key, block_type))
        filter_args = dict(
            course_id=course_key,
            module_type=block_type,
            modified__exact=modified_filter
        )
        if cohort:
            filter_args.update({
                'student__in': cohort.users.all().values_list('id', flat=True)
            })
        result = StudentModule.objects.filter(**filter_args)
        if len(self.user_enrollments_ignored_types):
            users = (
                CourseEnrollment.objects.all()
                                .filter(course_id=course_key, mode__in=self.user_enrollments_ignored_types)
                                .values_list('user', flat=True)
            )
            result = result.exclude(student__in=users)
        return result

    def get_progress_info_for_subsection(self, course_key, cohort):
        """
        Return activity for each of the section.
        """
        info = self.get_query_for_course_item_stat(course_key, 'sequential', cohort)
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
                        try:
                            subsection_info['children'][u['offset'] - 1]['student_count'] = u['count']
                        except IndexError as e:
                            log.error('Error occured while building a funnel chart, error message - {}'.format(e))
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

    def get_funnel_info(self, course_key, cohort):
        """
        Return course info in the tree-like structure.

        Structure of the node described inside function info_for_course_element.
        """
        subsection_activity = self.get_progress_info_for_subsection(course_key, cohort)
        courses_structure = self.get_course_info(course_key, subsection_activity)
        self.append_inout_info(courses_structure)
        return courses_structure

    def process(self, request, **kwargs):
        """
        Process post request.
        """
        return JsonResponse(data={'courses_structure': self.get_funnel_info(kwargs['course_key'], kwargs['cohort'])})
