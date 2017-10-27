from django.utils.translation import ugettext_noop

from courseware.access import has_access
from courseware.tabs import EnrolledTab
from xmodule.tabs import TabFragmentViewMixin


class InstructorAnalyticsDashboardTab(TabFragmentViewMixin, EnrolledTab):
    name = "instructor_analytics"
    type = "instructor_analytics"
    title = ugettext_noop("Instructor analytics")
    body_class = "instructor-analytics-tab"
    is_dynamic = True
    fragment_view_name = 'rg_instructor_analytics.views.InstructorAnalyticsFragmentView'

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Returns true if the specified user has staff access.
        """
        return bool(user and has_access(user, 'staff', course, course.id))
