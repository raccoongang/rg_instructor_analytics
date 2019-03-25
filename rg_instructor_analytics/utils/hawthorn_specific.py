"""
Helper file for inter-version compatibility.

This file and its sibling ginkgo_ficus_specific.py
serve for compatibility of rg_instructor_analytics app with both
ginkgo and hawthorn releases.
The following methods convert their arguments to make them usable in hawthorn release.
When the app is installed to hawthorn release, this file is imported wherever
there is version conflict.
The major changes between ginkgo and hawthorn releases, which affect the app are:
 - CourseEnrollment model: course_id changed from CourseKeyField to property
   that returns CourseKey object
 - StudentModule model: module_state_key was changed from LocationKeyField to UsageKeyField
"""


def get_problem_id(xblock):
    """
    Get Locator object for xblock.

    :param xblock: problem
    :return: Locator
    """
    return xblock.location


def get_problem_str(problem_id):
    """
    Get string form problem's Location.

    :param problem_id: Locator
    :return: string
    """
    return problem_id.to_deprecated_string()


def get_course_key(course_id):
    """
    Return CourseKey object without changes.

    :param course_id: CourseKey object
    :return: CourseKey object
    """
    return course_id
