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

from rg_instructor_analytics.models import GradeStatistic
from rg_instructor_analytics.utils.decorators import instructor_access_required

from courseware.courses import get_course_by_id
from rg_instructor_analytics_log_collector.models import VideoViewsByUser


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
        username = 'username'
        try:
            user_id = User.objects.get(username=username).id
        except User.DoesNotExist:
            return JsonResponse({'message': _("User with username {} does not exist").format(username)}, status=400)

        course_id = request.POST.get('course_id')
        course_key = CourseKey.from_string(course_id)
        course = get_course_by_id(course_key)

        video_views_by_user = VideoViewsByUser.objects.filter(course=course_key, user_id=user_id)

        video_names = []
        course_video_info = []

        for section in course.get_children():
            for sub_section in section.get_children():
                for unit in sub_section.get_children():
                    for block in unit.get_children():
                        if block.location.block_type == 'video':
                            video_names.append(block.display_name)
                            video_info = video_views_by_user.objects.filter(
                                video_block_id=block.location.block_id
                            ).first()
                            block_video_info = [video_info.viewed_time, video_info.is_complited] if video_info else [0, False]
                            course_video_info.append(block_video_info)

        return JsonResponse(
            data={
                'video_names': video_names,
                'course_video_info': course_video_info,
            }
        )
