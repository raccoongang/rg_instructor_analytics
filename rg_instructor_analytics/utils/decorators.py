import logging
from functools import wraps

from courseware.access import has_access
from courseware.courses import get_course
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.utils.decorators import available_attrs
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

log = logging.getLogger(__name__)


def instructor_access_required(view_func):
    """
    Decorator for views that checks that the user is logged in and has instructor access
    to the course with given course_id.
    """

    role = 'instructor'

    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
        course_id = request.POST.get('course_id')
        try:
            course_key = CourseKey.from_string(course_id)
            course = get_course(course_key)
            if not has_access(request.user, role, course):
                return HttpResponseForbidden(reason='Instructors only!')
            return view_func(request, *args, **kwargs)

        except (ValueError, InvalidKeyError):
            log.error(
                "Unable to find course with course key %s while loading the Instructor Analytics dashboard.",
                course_id
            )
            return HttpResponseBadRequest(reason='Bad course ID')
    return _wrapped_view
