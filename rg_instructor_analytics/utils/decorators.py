"""
Util decorators.
"""
from functools import wraps
import logging

from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.utils.decorators import available_attrs
from django.utils.translation import ugettext as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from courseware.access import has_access
from courseware.courses import get_course

log = logging.getLogger(__name__)


def instructor_access_required(view_func):
    """
    Instructor access check decorator.

    Decorator for views that checks the user is logged in and has instructor access
    to the course with given course_id.
    """
    role = 'staff'

    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
        course_id = request.POST.get('course_id') or kwargs.get('course_id')
        try:
            course_key = CourseKey.from_string(course_id)
            course = get_course(course_key)
            if not has_access(request.user, role, course):
                return HttpResponseForbidden(reason='Instructors only!')
            return view_func(request, *args, **kwargs)

        except InvalidKeyError:
            log.error(
                "Unable to find course with course key %s while loading the Instructor Analytics dashboard.",
                course_id
            )
            return HttpResponseBadRequest(reason=_("Invalid course ID."))
        except ValueError as exc:
            log.error(exc.message, course_id)
            return HttpResponseBadRequest(reason=exc.message)
    return _wrapped_view


def cohort_leader_access_required(view_func):
    """
    Cohort Leader access check decorator.

    Decorator for views that checks the user is logged in and has cohort leader access
    to the cohort with given cohort_id.
    """
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):
        cohort_id = request.POST.get('cohort_id') or kwargs.get('cohort_id')
        user = request.user
        if not getattr(user, 'profile') or not user.profile.cohort_leader.filter(id=cohort_id).exists():
            return HttpResponseForbidden(reason='Cohort Leaders only!')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
