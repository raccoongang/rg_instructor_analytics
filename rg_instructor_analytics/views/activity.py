"""
Gradebook sub-tab module.
"""
from datetime import datetime

from django.http import HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from rg_instructor_analytics.utils.decorators import instructor_access_required

from rg_instructor_analytics_log_collector.models import VideoViewsByDay, DiscussionActivityByDay


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

    def get_daily_activity_for_course(self, from_timestamp, to_timestamp, course_key):
        """
        Get statistic of video and discussion activities by days.
        """
        from_date = datetime.fromtimestamp(from_timestamp).date()
        to_date = datetime.fromtimestamp(to_timestamp).date()

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

        if to_date not in video_dates:
            video_dates.append(to_date)
            video_activities.append(0)

        discussion_activities_set = DiscussionActivityByDay.objects.filter(
            course=course_key,
            day__range=(from_date, to_date),
        ).order_by('day')

        discussion_dates = list(discussion_activities_set.values_list('day', flat=True))
        discussion_activities = list(discussion_activities_set.values_list('total', flat=True))

        return {
            'video_dates': video_dates,
            'video_activities': video_activities,
            'discussion_dates': discussion_dates,
            'discussion_activities': discussion_activities,
        }

    def post(self, request, course_id):
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

        return JsonResponse(
            data=self.get_daily_activity_for_course(from_timestamp, to_timestamp, course_key)
        )
