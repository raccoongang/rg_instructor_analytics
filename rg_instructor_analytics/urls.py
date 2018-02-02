"""
Url config file.
"""
from django.conf.urls import url

from rg_instructor_analytics.views import (
    CohortSendMessage, CohortView, EnrollmentStatisticView, GradebookView, InstructorAnalyticsFragmentView,
    ProblemDetailView, ProblemHomeWorkStatisticView, ProblemQuestionView, ProblemsStatisticView
)

urlpatterns = [
    url(r'^api/enroll_statics/$', EnrollmentStatisticView.as_view(), name='enrollment_statistic_view'),

    url(
        r'^api/problem_statics/homework/$',
        ProblemHomeWorkStatisticView.as_view(),
        name='problem_homework_statistic_view'
    ),

    url(r'^api/problem_statics/homeworksproblems/$', ProblemsStatisticView.as_view(), name='problems_statistic_view'),

    url(r'^api/problem_statics/problem_detail/$', ProblemDetailView.as_view(), name='problem_detail_view'),

    url(r'^api/problem_statics/problem_question_stat/$', ProblemQuestionView.as_view(), name='problem_question_view'),

    url(r'^api/gradebook/$', GradebookView.as_view(), name='gradebook_view'),

    url(r'^api/cohort/$', CohortView.as_view(), name='cohort_view'),

    url(r'^api/cohort/send_email/$', CohortSendMessage.as_view(), name='send_email_to_cohort'),

    url(r'^', InstructorAnalyticsFragmentView.as_view(), name='instructor_analytics_dashboard'),
]
