"""
Url config file.
"""
from django.conf.urls import url

from rg_instructor_analytics.views.cohort import CohortSendMessage, CohortView
from rg_instructor_analytics.views.enrollment import EnrollmentStatisticView
from rg_instructor_analytics.views.funnel import GradeFunnelView
from rg_instructor_analytics.views.gradebook import GradebookView
from rg_instructor_analytics.views.problem import (
    ProblemDetailView, ProblemHomeWorkStatisticView, ProblemQuestionView, ProblemsStatisticView
)
from rg_instructor_analytics.views.suggestion import SuggestionView
from rg_instructor_analytics.views.tab_fragment import instructor_analytics_dashboard

urlpatterns = [
    # Enrollment stats tab:
    url(r'^api/enroll_statics/$', EnrollmentStatisticView.as_view(), name='enrollment_statistic_view'),

    # Problems tab:
    url(
        r'^api/problem_statics/homework/$',
        ProblemHomeWorkStatisticView.as_view(),
        name='problem_homework_statistic_view'
    ),
    url(
        r'^api/problem_statics/homeworksproblems/$',
        ProblemsStatisticView.as_view(),
        name='problems_statistic_view'
    ),
    url(
        r'^api/problem_statics/problem_detail/$',
        ProblemDetailView.as_view(),
        name='problem_detail_view'
    ),
    url(
        r'^api/problem_statics/problem_question_stat/$',
        ProblemQuestionView.as_view(),
        name='problem_question_view'
    ),

    # Gradebook tab:
    url(r'^api/gradebook/$', GradebookView.as_view(), name='gradebook_view'),

    # Clusters tab:
    url(r'^api/cohort/$', CohortView.as_view(), name='cohort_view'),
    url(r'^api/cohort/send_email/$', CohortSendMessage.as_view(), name='send_email_to_cohort'),

    # Progress Funnel tab:
    url(r'^api/funnel/$', GradeFunnelView.as_view(), name='funnel'),

    # Suggestions tab:
    url(r'^api/suggestion/$', SuggestionView.as_view(), name='suggestion'),

    url(r'^$', instructor_analytics_dashboard, name='instructor_analytics_dashboard'),
]
