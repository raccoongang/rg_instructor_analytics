from django.conf.urls import url

from .views import InstructorAnalyticsFragmentView, EnrollmentStatisticView

urlpatterns = [
    url(r'^api/enroll_statics/$', EnrollmentStatisticView.as_view(), name='enrollment_statistic_view'),
    url(r'^', InstructorAnalyticsFragmentView.as_view(), name='instructor_analytics_dashboard'),
]
