"""
Util package.
"""
import os

import pkg_resources


def resource_string(path):
    """
    Handy helper for getting resources.
    """
    data = pkg_resources.resource_string(
        __name__,
        os.path.join('..', 'static', 'rg_instructor_analytics', path)
    )
    return data.decode("utf8")


def parse_coupled_id(coupled_id):
    """
    Parse the course_id and cohort_id from the coupled id.
    """
    if coupled_id is None:
        coupled_id = ''

    request_coupled_id = coupled_id.split('###')

    if len(request_coupled_id) == 1:
        request_coupled_id.append(0)
    elif request_coupled_id[1] == '':
        request_coupled_id[1] = 0

    return request_coupled_id
