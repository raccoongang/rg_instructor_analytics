"""
Gradebook sub-tab module.
"""
from datetime import datetime, timedelta

from django.db.models import Count
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rg_instructor_analytics_log_collector.models import (
    CourseVisitsByDay, DiscussionActivityByDay, StudentStepCourse, VideoViewsByDay
)

from lms.djangoapps.courseware.courses import get_course_by_id
from rg_instructor_analytics.utils.decorators import instructor_access_required


class ActivityView(View):
    """
    Activities API view.
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(ActivityView, self).dispatch(*args, **kwargs)

    def get_daily_activity_for_course(self, from_date, to_date, course_key):
        """
        Get statistic of video and discussion activities by days.
        """
        video_dates = []
        video_activities = []

        video_activities_data = list(VideoViewsByDay.objects.filter(
            course=course_key,
            day__range=(from_date, to_date)
        ).order_by('day').values_list('day', 'total'))

        for v_day, v_total in video_activities_data:
            if v_day not in video_dates:
                video_dates.append(v_day)
                video_activities.append(v_total)
            else:
                video_activities[-1] += v_total

        if from_date not in video_dates:
            video_dates.insert(0, from_date)
            video_activities.insert(0, 0)

        if to_date - timedelta(1) not in video_dates:
            video_dates.append(to_date - timedelta(1))
            video_activities.append(0)

        if to_date not in video_dates:
            video_dates.append(to_date)
            video_activities.append(0)

        discussion_data = DiscussionActivityByDay.objects.filter(
            course=course_key,
            day__range=(from_date, to_date),
        ).order_by('day').values('day', 'total')

        discussion_dates = []
        discussion_activities = []
        for d in discussion_data:
            discussion_dates.append(d['day'])
            discussion_activities.append(d['total'])

        course_visits_data = CourseVisitsByDay.objects.filter(
            course=course_key,
            day__range=(from_date, to_date),
        ).order_by('day').values('day', 'total')

        course_dates = []
        course_activities = []
        for d in course_visits_data:
            course_dates.append(d['day'])
            course_activities.append(d['total'])

        activities = video_activities + discussion_activities + course_activities
        nticks_y = max(activities) if activities else 0
        customize_yticks = True if nticks_y <= 3 else False  # y-axis

        return {
            'video_dates': video_dates,
            'video_activities': video_activities,
            'discussion_dates': discussion_dates,
            'discussion_activities': discussion_activities,
            'course_dates': course_dates,
            'course_activities': course_activities,
            'customize_yticks': customize_yticks,
            'nticks_y': nticks_y,
        }

    def get_unit_visits(self, from_date, to_date, course_key):
        """
        Get statistic of visiting units.
        """
        course = get_course_by_id(course_key, depth=3)

        ticktext = []
        tickvals = []
        count_visits = []

        def _make_query(field_name):
            """
            Create aggregated query and return it's result

            Query format is:
                SELECT <field_name>, COUNT(<field_name>) AS <field_name>__count
                FROM rg_instructor_analytics_log_collector_studentstepcourse
                WHERE (course = '<course_key>' AND log_time BETWEEN '<start_date>' AND '<end_date>')
                GROUP BY <field_name>

            :param field_name: field that contain unit id, could be 'current_unit' or 'target_unit'
            :return: dict, {<unit_id>: <count>}
            """
            qs = StudentStepCourse.objects.filter(
                course=course_key,
                log_time__range=(from_date, to_date + timedelta(days=1))
            )
            qs = qs.values(field_name).annotate(Count(field_name))
            return dict(qs.values_list(field_name, '{}__count'.format(field_name)))

        # 'current_unit' mean user leave unit, 'target_unit' mean user come to unit
        counted_current_units = _make_query('current_unit')
        counted_target_units = _make_query('target_unit')

        for section in course.get_children():
            for subsection in section.get_children():
                for unit in subsection.get_children():
                    tickvals.append(unit.location.block_id)
                    ticktext.append(unit.display_name)
                    # we could have some missed events like 'Start Course' click or go to subsection from Course Outline
                    # so why we select highest value from current_unit and target_unit counts
                    count_visits.append(
                        max(
                            counted_current_units.get(unit.location.block_id, 0),
                            counted_target_units.get(unit.location.block_id, 0)
                        )
                    )

        return {
            'ticktext': ticktext,
            'tickvals': tickvals,
            'count_visits': count_visits
        }

    def post(self, request, course_id, slug):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        try:
            from_timestamp = int(request.POST.get('from'))
            to_timestamp = int(request.POST.get('to'))
            course_key = CourseKey.from_string(request.POST.get('course_id'))

        except (TypeError, ValueError):
            return HttpResponseBadRequest(_("Invalid date range."))
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        from_date = datetime.fromtimestamp(from_timestamp).date()
        to_date = datetime.fromtimestamp(to_timestamp).date()

        if slug == 'daily':
            activity = self.get_daily_activity_for_course(from_date, to_date, course_key)
        elif slug == 'unit_visits':
            activity = self.get_unit_visits(from_date, to_date, course_key)
        else:
            activity = {}

        return JsonResponse(data={
            'activity': activity

        })
