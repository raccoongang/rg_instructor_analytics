"""
Util package.
"""
import os

import pkg_resources
from django.db.models import Q
from django.contrib.auth.models import User
from student.roles import CourseCreatorRole, CourseInstructorRole, CourseStaffRole


def resource_string(path):
    """
    Handy helper for getting resources.
    """
    data = pkg_resources.resource_string(
        __name__,
        os.path.join('..', 'static', 'rg_instructor_analytics', path)
    )
    return data.decode("utf8")


def get_course_instructors_ids(course_key):
    """Return UID`s for all course instructors and staff."""
    is_instructor = Q(
        courseaccessrole__course_id=course_key,
        courseaccessrole__role__in=(
            CourseStaffRole.ROLE,
            CourseInstructorRole.ROLE,
            CourseCreatorRole.ROLE,
        )
    )
    is_staff = Q(is_staff=True)

    return list(User.objects.filter(is_staff | is_instructor).distinct().values_list('id', flat=True))
