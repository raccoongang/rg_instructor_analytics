from opaque_keys.edx.keys import CourseKey


def get_problem_id(xblock):
    """
    rg_instructor_analytics/views/problem.py: line 123
    problem_id = child.location.to_deprecated_string()
    """
    return xblock.location.to_deprecated_string()


def get_problem_str(problem_id):
    """
    rg_instructor_analytics/views/problem.py: line 129
    stats['problems'][-1].append(problem_id)

    rg_instructor_analytics/views/funnel.py: line 151
    if info['module_state_key'] not in result:
        result[info['module_state_key']] = []
    result[info['module_state_key']].append({ ...
    """
    return problem_id


def get_course_key(course_id):
    """
    rg_instructor_analytics/tasks.py: line 98
    try:
        course_key = CourseKey.from_string(item['course_id'])
    except InvalidKeyError:
        continue
    """
    return CourseKey.from_string(course_id)
