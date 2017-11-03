"""Url config file."""
from django.conf.urls import url

from rg_instructor_analytics.views import EnrollmentStatisticView, InstructorAnalyticsFragmentView

urlpatterns = [
    url(r'^api/enroll_statics/$', EnrollmentStatisticView.as_view(), name='enrollment_statistic_view'),
    url(r'^', InstructorAnalyticsFragmentView.as_view(), name='instructor_analytics_dashboard'),
]
