"""
Module for handle tracker events.
"""
from abc import ABCMeta, abstractmethod

from django.db import transaction
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from track.backends import BaseBackend

from rg_instructor_analytics.models import EnrollmentByStudent, EnrollmentTabCache


class StatisticProcessor(object):
    """
    Base class for process statistic item.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def process(self, event):
        """
        Process log event.

        Attention - don`t modify event object.
        """
        pass

    @staticmethod
    def get_event_timestamp(event):
        """
        Return timestamp of the event.
        """
        return event['time'] if 'time' in event else event['timestamp']

    @staticmethod
    def get_event_name(event):
        """
        Return name of the event.
        """
        if 'event_type' in event:
            return event['event_type']
        return event['name']

    @staticmethod
    def get_event_user_id(event):
        """
        Return of the user from the event.
        """
        return event.get('context', {}).get('user_id', None)

    @staticmethod
    def get_course_id(event):
        """
        Return CourseKey object, based on the course_id from the event.
        """
        string_id = event.get('context', {}).get('course_id', None)
        if string_id:
            try:
                return CourseKey.from_string(string_id)
            except InvalidKeyError:
                return


class EnrollmentProcessor(StatisticProcessor):
    """
    Class for the enrollment event processing.
    """

    status_map = {
        'edx.course.enrollment.deactivated': False,
        'edx.course.enrollment.activated': True,
    }

    def get_exist_stat(self, user_id, course_id, event_time):
        """
        Return tuple with EnrollmentTabCache and EnrollmentByStudent.
        """
        last_course_update = (
            EnrollmentTabCache.objects.filter(course_id=course_id).order_by('-created').first()
        )

        enrollment_cache, _ = EnrollmentTabCache.objects.get_or_create(
            course_id=course_id,
            created=event_time.date(),
            defaults={
                'total': last_course_update and last_course_update.total or 0
            }

        )
        student_history, _ = EnrollmentByStudent.objects.get_or_create(
            course_id=course_id,
            student=user_id
        )
        return enrollment_cache, student_history

    def process(self, event):
        """
        Process enrollment information from the event.
        """
        status = self.status_map.get(self.get_event_name(event), None)
        if status is None:
            return
        user_id = self.get_event_user_id(event)
        course_id = self.get_course_id(event)
        if not (user_id and course_id):
            return

        event_time = self.get_event_timestamp(event)

        with transaction.atomic():
            enrollment_cache, student_history = self.get_exist_stat(user_id, course_id, event_time)
            if student_history.last_update is None or student_history.last_update.date() < event_time.date():
                enrollment_cache.enroll += status
                enrollment_cache.unenroll += not status
                enrollment_cache.total += status
            elif student_history.state != status:
                enrollment_cache.enroll += status and 1 or -1
                enrollment_cache.unenroll += status and -1 or 1
                enrollment_cache.total += status and 1 or -1

            student_history.state = status
            student_history.last_update = event_time

            student_history.save()
            enrollment_cache.save()


class TrackingBackend(BaseBackend):
    """
    Backend for collect tracked event.
    """

    def __init__(self, **kwargs):
        """
        Init event.
        """
        super(TrackingBackend, self).__init__(**kwargs)

        self.statistic_processors = [
            EnrollmentProcessor()
        ]

    def send(self, event):
        """
        Process event.
        """
        for processor in self.statistic_processors:
            processor.process(event)
