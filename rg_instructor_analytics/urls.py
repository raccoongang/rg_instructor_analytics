from django.conf.urls import patterns, url

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
        EnrollmentStatisticView.as_view(),
        name='enrollment_statistic_view'
    ),
)
