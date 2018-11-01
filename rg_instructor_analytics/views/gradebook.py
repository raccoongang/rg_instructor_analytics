"""
Gradebook sub-tab module.
"""
from collections import OrderedDict
import json

from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.courseware.courses import get_course_by_id

import django_comment_client.utils as utils

from rg_instructor_analytics.models import GradeStatistic
from rg_instructor_analytics.utils.decorators import instructor_access_required

from rg_instructor_analytics_log_collector.models import DiscussionActivity, VideoViewsByUser


class GradebookView(View):
    """
    Gradebook API view.

    Source: modulestore (MongoDB) periodic task
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(GradebookView, self).dispatch(*args, **kwargs)

    @staticmethod
    def post(request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        try:
            filter_string = request.POST.get('filter')
            stats_course_id = request.POST.get('course_id')
            course_key = CourseKey.from_string(stats_course_id)

        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        enrolled_students = GradeStatistic.objects.filter(course_id=course_key)
        if filter_string:
            enrolled_students = enrolled_students.filter(
                Q(student__username__icontains=filter_string)
                | Q(student__first_name__icontains=filter_string)
                | Q(student__last_name__icontains=filter_string)
                | Q(student__email__icontains=filter_string)
            )
        enrolled_students = enrolled_students\
            .order_by('student__username')\
            .values('student__username', 'exam_info')

        student_info = [
            json.JSONDecoder(object_pairs_hook=OrderedDict).decode(student['exam_info'])
            for student in enrolled_students
        ]
        students_names = [student['student__username'] for student in enrolled_students]
        exam_names = list(student_info[0].keys()) if len(student_info) > 0 else []

        return JsonResponse(
            data={
                'student_info': student_info,
                'exam_names': exam_names,
                'students_names': students_names,
            }
        )


class VideoView(View):
    """
    Video Views API view.
    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(VideoView, self).dispatch(*args, **kwargs)

    @staticmethod
    def post(request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        try:
            user = User.objects.get(username=request.POST.get('username'))
        except (InvalidKeyError, User.DoesNotExist):
            return HttpResponseBadRequest(_("Invalid username."))

        try:
            course_key = CourseKey.from_string(request.POST.get('course_id'))
            course = get_course_by_id(course_key, depth=4)
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        video_views_by_user = VideoViewsByUser.objects.filter(course=course_key, user_id=user.id)

        videos_names = []
        videos_time = []
        videos_completed = []

        for section in course.get_children():
            for sub_section in section.get_children():
                for unit in sub_section.get_children():
                    for block in unit.get_children():
                        if block.location.block_type == 'video':
                            video_name = block.display_name
                            while video_name in videos_names:
                                video_name = video_name + '1'
                            videos_names.append(video_name)
                            video_info = video_views_by_user.filter(
                                video_block_id=block.location.block_id
                            ).first()
                            if video_info:
                                video_time = video_info.viewed_time
                                video_is_completed = video_info.is_completed
                            else:
                                video_time = 0
                                video_is_completed = False
                            videos_time.append(video_time)
                            videos_completed.append(video_is_completed)

        return JsonResponse(
            data={
                'videos_names': videos_names,
                'videos_time': videos_time,
                'videos_completed': videos_completed,
            }
        )


class DiscussionActivityView(View):
    """
    DiscussionActivityView API view.

    """

    @method_decorator(instructor_access_required)
    def dispatch(self, *args, **kwargs):
        """
        See: https://docs.djangoproject.com/en/1.8/topics/class-based-views/intro/#id2.
        """
        return super(DiscussionActivityView, self).dispatch(*args, **kwargs)

    @staticmethod
    def post(request, course_id):
        """
        POST request handler.

        :param course_id: (str) context course ID (from urlconf)
        """
        try:
            user = User.objects.get(username=request.POST.get('username'))
        except (InvalidKeyError, User.DoesNotExist):
            return HttpResponseBadRequest(_("Invalid username."))

        try:
            course_key = CourseKey.from_string(request.POST.get('course_id'))
            course = get_course_by_id(course_key)
        except InvalidKeyError:
            return HttpResponseBadRequest(_("Invalid course ID."))

        thread_names = []
        activity_count = []

        category_map = utils.get_discussion_category_map(course, user)

        discussion_activities = DiscussionActivity.objects.filter(
            user_id=user.id,
            course=course_key
        )

        for thread_name, thread_type in category_map.get('children', []):
            if thread_type == 'entry':
                thread_id = category_map.get('entries', {}).get(thread_name, {}).get('id')
                thread_names.append(thread_name)
                activity_count.append(discussion_activities.filter(commentable_id=thread_id).count())
            elif thread_type == 'subcategory':
                subcategory = category_map.get('subcategories', {}).get(thread_name, {})

                for thread_subcategory_name, thread_subcategory_type in subcategory.get('children', []):
                    thread_id = subcategory.get('entries', {}).get(thread_subcategory_name, {}).get('id')
                    thread_names.append('{} / {}'.format(thread_name, thread_subcategory_name))
                    activity_count.append(discussion_activities.filter(commentable_id=thread_id).count())

        return JsonResponse(
            data={
                'thread_names': thread_names,
                'activity_count': activity_count,
            }
        )
