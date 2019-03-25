"""
Helper file for inter-version compatibility.

This file and its sibling hawthorn_specific.py
serve for compatibility of rg_instructor_analytics app with both
ginkgo and hawthorn releases.
The following methods convert their arguments to make them usable in
ginkgo and ficus releases. When the app is installed to ginkgo or ficus release,
this file is imported wherever there is version conflict.
The major changes between ginkgo and hawthorn releases, which affect the app are:
 - CourseEnrollment model: course_id changed from CourseKeyField to property
   that returns CourseKey object
 - StudentModule model: module_state_key was changed from LocationKeyField to UsageKeyField
"""

from opaque_keys.edx.keys import CourseKey


def get_problem_id(xblock):
    """
    Convert xblock's location to string.

    :param xblock: problem
    :return: problem Locator object
    """
    return xblock.location.to_deprecated_string()


def get_problem_str(problem_id):
    """
    Return problem location string unchanged.

    :param problem_id: problem location string
    :return: problem location string
    """
    return problem_id


def get_course_key(course_id):
    """
    Convert string to CourseKey object.

    :param course_id: string
    :return: CourseKey object
    """
    return CourseKey.from_string(course_id)
