from django.conf.urls import patterns, url

from .views import CalendarTabFragmentView

urlpatterns = patterns(
    'rg_instructor_analytics.views',
    url(
        r'^$',
        CalendarTabFragmentView.as_view(),
        name='calendar_tab_fragment_view'
    ),
)
