from django.conf.urls import patterns, url

from instructor.views.api import require_level
from .views import InstructorAnalyticsFragmentView, EnrollmentStatisticView

urlpatterns = patterns(
    '',
    url(
        r'^$',
        InstructorAnalyticsFragmentView.as_view(),
        name='instructor_analytics_dashboard'
    ),
    url(
        r'^api/enroll_statics$',
        require_level('staff')(EnrollmentStatisticView.as_view()),
        name='enrollment_statistic_view'
    ),
)
