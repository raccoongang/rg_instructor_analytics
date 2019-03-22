def get_problem_id(xblock):
    """
    rg_instructor_analytics/views/problem.py: line 123
    problem_id = child.location # hawthorn
    """
    return xblock.location


def get_problem_str(problem_id):
    """
    rg_instructor_analytics/views/problem.py: line 129
    stats['problems'][-1].append(problem_id.to_deprecated_string())

    rg_instructor_analytics/views/funnel.py: line 151
    if info['module_state_key'].to_deprecated_string() not in result:
        result[info['module_state_key'].to_deprecated_string()] = []
    result[info['module_state_key'].to_deprecated_string()].append({  # hawthorn
    """
    return problem_id.to_deprecated_string()


def get_course_key(course_id):
    """
    rg_instructor_analytics/tasks.py: line 98
    try:
        course_key = item['course_id']
    except InvalidKeyError:
        continue
    """
    return course_id
