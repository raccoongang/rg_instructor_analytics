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

logging.basicConfig()

log = logging.getLogger(__name__)


class AccessMixin(object):
    """
    Base class for provide check  user permission.
    """

    __metaclass__ = ABCMeta

    group_name = 'staff'

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
        course_id = request.POST.get('course_id') or course_id
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error("Unable to find course with course key %s while loading the Instructor Analytics Dashboard.",
                      course_id)
            return HttpResponseBadRequest()

        course = get_course_by_id(course_key, depth=0)
        if not has_access(request.user, self.group_name, course):
            log.error("Statistics not available for user type `%s`", request.user)
            return HttpResponseForbidden()

        return self.process(request, course_key=course_key, course=course, course_id=course_id)

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
