"""
Progress Funnel sub-tab module.
"""
from datetime import date, timedelta
import json

from django.db.models import Count, Q
from django.db.models.expressions import RawSQL
from django.http.response import HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from courseware.courses import get_course_by_id
from courseware.models import StudentModule
from rg_instructor_analytics import tasks
from rg_instructor_analytics.utils.decorators import instructor_access_required
from student.models import CourseEnrollment

try:
    from openedx.core.release import RELEASE_LINE
except ImportError:
    RELEASE_LINE = 'ficus'

if RELEASE_LINE == 'ficus' or RELEASE_LINE == 'ginkgo':
    from rg_instructor_analytics.utils import ginkgo_ficus_specific as specific
else:
    from rg_instructor_analytics.utils import hawthorn_specific as specific


IGNORED_ENROLLMENT_MODES = []


def course_element_info(element, level):
    """
    Return new element of the course item.
    """
    return {
        'level': level,
        'name': element.display_name,
        'id': element.location.to_deprecated_string(),
        'student_count': 0,
        'student_emails': [],
        'student_count_in': 0,
        'student_count_out': 0,
        'children': [],
    }


def add_as_child(element, child):
    """
    Append to dictionary new element, named children.
    """
    element['children'].append(child)


class GradeFunnelView(View):
    """
    Progress Funnel API view.

    Data source: StudentModule DB model.
    """

    # NOTE(wowkalucky): needs optimization - request takes above 30 sec!

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(GradeFunnelView, self).dispatch(*args, **kwargs)

    def post(self, request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        post_data = request.POST

        try:
            from_date = post_data.get('from') and date.fromtimestamp(float(post_data['from']))
            to_date = post_data.get('to') and date.fromtimestamp(float(post_data['to']))

            stats_course_id = request.POST.get('course_id')
            course_key = CourseKey.from_string(stats_course_id)

        except ValueError:
            return HttpResponseBadRequest(_("Invalid date range."))
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        return JsonResponse(data={'courses_structure': self.get_funnel_info(course_key, from_date, to_date)})

    @staticmethod
    def get_query_for_course_item_stat(course_key, block_type, from_date=None, to_date=None):
        """
        Build DB queryset for course block type and given course.
        """
        # TODO use preaggregation
        modified_filter = RawSQL(
            "(SELECT MAX(t2.modified) FROM courseware_studentmodule t2 " +
            "WHERE (t2.student_id = courseware_studentmodule.student_id) AND t2.course_id = %s "
            "AND t2.module_type = %s)", (course_key, block_type))

        date_range_filter = Q(modified__range=(
            from_date, to_date + timedelta(days=1))
        ) if from_date and to_date else Q()

        enrolled_by_course = CourseEnrollment.objects.filter(course_id=course_key).values_list('user__id', flat=True)
        students_course_state_qs = StudentModule.objects.filter(
            date_range_filter,
            course_id=course_key,
            module_type=block_type,
            modified__exact=modified_filter,
            student_id__in=enrolled_by_course
        )

        if IGNORED_ENROLLMENT_MODES:
            users = (
                CourseEnrollment.objects
                .filter(
                    course_id=course_key,
                    mode__in=IGNORED_ENROLLMENT_MODES
                )
                .values_list('user', flat=True)
            )
            students_course_state_qs = students_course_state_qs.exclude(student__in=users)

        return students_course_state_qs

    def get_progress_info_for_subsection(self, course_key, from_date=None, to_date=None):
        """
        Return activity for each of the section.
        """
        query_info = self.get_query_for_course_item_stat(course_key, 'sequential', from_date, to_date)
        dict_info = query_info.values(
            'module_state_key', 'state', 'student__email'
        ).order_by(
            'module_state_key', 'state'
        ).annotate(
            count=Count('module_state_key')
        ).values(
            'module_state_key', 'state', 'count', 'student__email'
        )
        result = {}

        for info in dict_info:
            if specific.get_problem_str(info['module_state_key']) not in result:
                result[specific.get_problem_str(info['module_state_key'])] = []

            result[specific.get_problem_str(info['module_state_key'])].append({
                'count': info['count'],
                'offset': json.loads(info['state'])['position'],
                'student_email': info['student__email']
            })
        return result

    @staticmethod
    def get_course_info(course_key, subsection_activity):
        """
        Return information about the course in tree view.
        """
        course_info = []
        course = get_course_by_id(course_key, depth=4)
        for section in course.get_children():
            section_info = course_element_info(section, level=0)
            for subsection in section.get_children():
                subsection_info = course_element_info(subsection, level=1)
                for unit in subsection.get_children():
                    unit_info = course_element_info(unit, level=2)
                    add_as_child(subsection_info, unit_info)
                add_as_child(section_info, subsection_info)

                if subsection_info['id'] in subsection_activity:
                    for progress_info in subsection_activity[subsection_info['id']]:
                        if subsection_info['children']:

                            try:
                                progress_unit = subsection_info['children'][progress_info['offset'] - 1]
                            except IndexError:
                                progress_unit = subsection_info['children'][-1]

                            progress_unit['student_count'] += progress_info['count']
                            progress_unit['student_emails'] += [progress_info['student_email']]

                            subsection_info['student_count'] += progress_info['count']
                            subsection_info['student_emails'] += [progress_info['student_email']]

                    section_info['student_count'] += subsection_info['student_count']
                    section_info['student_emails'] += subsection_info['student_emails']
            course_info.append(section_info)
        return course_info

    def append_inout_info(self, statistic, accomulate=0):
        """
        Append information about how many students in course.
        """
        for i in reversed(statistic):
            i['student_count_out'] = accomulate
            if len(i['children']):
                self.append_inout_info(i['children'], accomulate=accomulate)
            accomulate += i['student_count']
            i['student_count_in'] = accomulate

    def get_funnel_info(self, course_key, from_date=None, to_date=None):
        """
        Return course info in the tree-like structure.

        Structure of the node described inside function course_element_info.
        """
        subsection_activity = self.get_progress_info_for_subsection(course_key, from_date, to_date)
        courses_structure = self.get_course_info(course_key, subsection_activity)
        self.append_inout_info(courses_structure)
        return courses_structure


class GradeFunnelSendMessage(View):
    """
    Endpoint for sending email message.
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(GradeFunnelSendMessage, self).dispatch(*args, **kwargs)

    def post(self, request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        emails = request.POST.get('emails')
        email_subject = request.POST.get('subject')
        email_body = request.POST.get('body')

        email_list = list(set([email for email in emails.split(',') if email]))

        tasks.send_email.delay(
            subject=email_subject,
            message=email_body,
            students=email_list
        )
        return JsonResponse({'status': 'ok'})
