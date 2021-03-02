"""
Module for tabs description.
"""
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.utils.translation import ugettext_noop

from courseware.access import has_access
from xmodule.tabs import CourseTab
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


class InstructorAnalyticsDashboardTab(CourseTab):
    """
    Provides information for tab.
    """

    name = "instructor_analytics"
    type = "instructor_analytics"
    title = ugettext_noop("Instructor analytics")
    body_class = "instructor-analytics-tab"
    is_dynamic = True
    fragment_view_name = 'rg_instructor_analytics.views.tab_fragment.instructor_analytics_dashboard'
    view_name = 'instructor_analytics_dashboard'

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Return true if the specified user has staff access.
        """
        return bool(
            user and
            has_access(user, 'staff', course, course.id) and
            configuration_helpers.get_value(
                'ENABLE_RG_INSTRUCTOR_ANALYTICS',
                settings.FEATURES.get('ENABLE_RG_INSTRUCTOR_ANALYTICS', False)
            )
        )

    def __init__(self, tab_dict):
        """
        Counstruct tab.
        """
        super(InstructorAnalyticsDashboardTab, self).__init__(tab_dict)
        self._fragment_view = None

    @property
    def url_slug(self):
        """
        Return the slug to be included in this tab's URL.
        """
        return "tab/{}".format(self.type)

    @property
    def fragment_view(self):
        """
        Return the view that will be used to render the fragment.
        """
        if not self._fragment_view:
            self._fragment_view = get_storage_class(self.fragment_view_name)()
        return self._fragment_view

    def render_to_fragment(self, request, course, **kwargs):
        """
        Render this tab to a web fragment.
        """
        return self.fragment_view.render_to_fragment(request, course_id=unicode(course.id), **kwargs)


class CohortReportDashboardTab(InstructorAnalyticsDashboardTab):
    name = "cohort_report"
    type = "cohort_report"
    title = ugettext_noop("Cohort Report")
    body_class = "cohort-report-tab"
    is_dynamic = True
    fragment_view_name = 'rg_instructor_analytics.views.tab_fragment.cohort_report_dashboard'
    view_name = 'cohort_report_dashboard'
    priority = 100

    def __init__(self, tab_dict):
        """
        Counstruct tab.
        """
        super(CohortReportDashboardTab, self).__init__(tab_dict)
        self._fragment_view = None

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Return true if the specified user has staff access.
        """
        return bool(
            user and
            user.profile.cohort_leader.count() > 0 and
            (
                configuration_helpers.get_value(
                    'ENABLE_RG_INSTRUCTOR_ANALYTICS',
                    settings.FEATURES.get('ENABLE_RG_INSTRUCTOR_ANALYTICS', False)
                ) and configuration_helpers.get_value(
                    'ENABLE_COHORT_REPORTS',
                    settings.FEATURES.get('ENABLE_COHORT_REPORTS', False)
                )
            ))
