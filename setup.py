"""Setup file."""

import os
from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="rg_instructor_analytics",
    version="0.1",
    install_requires=[
        "setuptools",
        "web-fragments==0.2.2",
    ],
    requires=[],
    packages=["rg_instructor_analytics"],
    description='Open Edx Instructor analytics tab',
    long_description=README,
    entry_points={
        "openedx.course_tab": [
            "instructor_analytics = rg_instructor_analytics.plugins:InstructorAnalyticsDashboardTab"
        ],
    }
)
