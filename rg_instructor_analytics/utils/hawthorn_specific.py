def get_problem_id(xblock):
    return xblock.location


def get_problem_str(problem_id):
    return problem_id.to_deprecated_string()


def get_course_key(course_id):
    return course_id
