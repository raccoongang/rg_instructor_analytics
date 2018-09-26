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
