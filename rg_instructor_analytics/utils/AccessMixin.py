"""
Module for access mixin.
"""
from abc import ABCMeta, abstractmethod
import logging

from django.http import HttpResponseBadRequest
from django.http.response import HttpResponseForbidden
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from courseware.access import has_access
from courseware.courses import get_course_by_id
from openedx.core.djangoapps.course_groups import cohorts
from django.core.exceptions import ObjectDoesNotExist

logging.basicConfig()

log = logging.getLogger(__name__)


class AccessMixin(object):
    """
    Base class for provide check  user permission.
    """

    __metaclass__ = ABCMeta

    group_name = 'staff'
    course_cohorts = None

    def get_course_cohorts(self, user, course):
        course_cohorts = cohorts.get_course_cohorts(course)
        if user.is_superuser:
            self.course_cohorts = [c.name for c in cohorts.get_course_cohorts(course)]
        else:
            for cohort in course_cohorts:
                if [user.username, course.id.to_deprecated_string()] == cohort.name.split()[:-1]:
                    self.course_cohorts = [cohort.name]

    @abstractmethod
    def process(self, request, **kwargs):
        """
        Process allowed request.
        """
        pass

    def base_process(self, request, course_id):
        """
        Preprocess request, check permission and select course.
        """
        course_id = request.POST.get('course_id', course_id)
        reset_cohort = request.POST.get('reset_cohort')
        cohort_name = None if reset_cohort else request.POST.get('cohort')
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error("Unable to find course with course key %s while loading the Instructor Analytics Dashboard.",
                      course_id)
            return HttpResponseBadRequest()

        cohort = cohorts.get_cohort_by_name(course_key, cohort_name) if cohort_name else None

        course = get_course_by_id(course_key, depth=0)
        # set cohorts ones for all views
        self.get_course_cohorts(request.user, course)
        if not has_access(request.user, self.group_name, course):
            log.error("Statistics not available for user type `%s`", request.user)
            return HttpResponseForbidden()

        return self.process(request, course_key=course_key, course=course, course_id=course_id, cohort=cohort)

    def post(self, request, course_id):
        """
        Overwrite base method for process post request.
        """
        return self.base_process(request, course_id)

    def render_to_fragment(self, request, course_id):
        """
        Overwrite base method for process render to fragment.
        """
        return self.base_process(request, course_id)
