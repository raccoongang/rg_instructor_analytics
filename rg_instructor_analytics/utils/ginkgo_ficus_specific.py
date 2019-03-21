from opaque_keys.edx.keys import CourseKey


def get_problem_id(xblock):
    return xblock.location.to_deprecated_string()


def get_problem_str(problem_id):
    return problem_id


def get_course_key(course_id):
    return CourseKey.from_string(course_id)