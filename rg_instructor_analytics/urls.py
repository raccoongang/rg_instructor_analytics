"""
Url config file.
"""
from django.conf.urls import url

from rg_instructor_analytics.views import (
    EnrollmentStatisticView, GradebookView, InstructorAnalyticsFragmentView, ProblemDetailView,
    ProblemHomeWorkStatisticView, ProblemQuestionView, ProblemsStatisticView
)

urlpatterns = [
    url(r'^api/enroll_statics/$', EnrollmentStatisticView.as_view(),
        name='enrollment_statistic_view'),
    url(r'^api/problem_statics/homework/$', ProblemHomeWorkStatisticView.as_view(),
        name='problem_homework_statistic_view'),
    url(r'^api/problem_statics/homeworksproblems/$', ProblemsStatisticView.as_view(),
        name='problems_statistic_view'),
    url(r'^api/problem_statics/problem_detail/$', ProblemDetailView.as_view(),
        name='problem_detail_view'),
    url(r'^api/problem_statics/problem_question_stat/$', ProblemQuestionView.as_view(),
        name='problem_question_view'),
    url(r'^api/gradebook/$', GradebookView.as_view(),
        name='gradebook_view'),
    url(r'^', InstructorAnalyticsFragmentView.as_view(),
        name='instructor_analytics_dashboard'),
]
