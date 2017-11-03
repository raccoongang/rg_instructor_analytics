from datetime import date

from django.http.request import QueryDict
from django.test import TestCase, RequestFactory
from opaque_keys import InvalidKeyError

from mock import patch, Mock

from rg_instructor_analytics.views import EnrollmentStatisticView


class TestEnrollmentStatisticView(TestCase):
    """
    Test for enrollment statistic view
    """

    MOCK_PREVIOUS_ENROLL_STATE = (4, -1)
    MOCK_CURRENT_ENROLL_STATE = [
        {'date': date(2017, 10, 6), 'count': 1, 'is_active': False},
        {'date': date(2017, 10, 7), 'count': 1, 'is_active': False},
        {'date': date(2017, 10, 8), 'count': 2, 'is_active': False},
        {'date': date(2017, 10, 8), 'count': 1, 'is_active': True},
        {'date': date(2017, 10, 14), 'count': 1, 'is_active': True},
        {'date': date(2017, 10, 20), 'count': 1, 'is_active': True},
        {'date': date(2017, 10, 23), 'count': 1, 'is_active': True},
    ]
    MOCK_FROM_DATE = 1507150800
    MOCK_TO_DATE = 1509573600
    MOCK_REQUEST_PARAMS = QueryDict('from=' + str(MOCK_FROM_DATE) + '&to=' + str(MOCK_TO_DATE))
    MOCK_COURSE_ID = 'course-v1:test+course+id'
    MOCK_ALLOWED_USER = 'staff'
    MOCK_UN_ALLOWED_USER = 'honor'

    EXPECTED_ENROLL_STATISTIC = {
        'dates': [1507150800, 1507262400, 1507348800, 1507435200, 1507953600, 1508472000, 1508731200, 1509573600],
        'total': [3, 2, 1, 0, 1, 2, 3, 3],
        'enroll': [4, 4, 4, 5, 6, 7, 8, 8],
        'unenroll': [-1, -2, -3, -5, -5, -5, -5, -5],
    }

    def setUp(self):
        """
        Setup for test
        """
        self.factory = RequestFactory()

    @patch('rg_instructor_analytics.views.has_access')
    @patch('rg_instructor_analytics.views.get_course_by_id')
    @patch('rg_instructor_analytics.views.CourseKey.from_string')
    @patch('rg_instructor_analytics.views.EnrollmentStatisticView.get_statistic_per_day')
    def test_enroll_statistic_post_call(
            self, moc_get_statistic_per_day,
            moc_course_key_from_string,
            moc_get_course_by_id,
            moc_has_access):
        """
        Verify standard post flow
        """
        moc_get_statistic_per_day.return_value = self.EXPECTED_ENROLL_STATISTIC
        moc_course_key_from_string.return_value = 'key'
        moc_get_course_by_id.return_value = 'course'
        moc_has_access.return_value = True

        request = self.factory.post('/courses/' + self.MOCK_COURSE_ID + '/tab/instructor_analytics/api/enroll_statics/')
        request.user = self.MOCK_ALLOWED_USER
        request.POST = self.MOCK_REQUEST_PARAMS

        response = EnrollmentStatisticView.as_view()(request, course_id=self.MOCK_COURSE_ID)

        self.assertEqual(response.status_code, 200)
        moc_course_key_from_string.assert_called_once_with(self.MOCK_COURSE_ID)
        moc_has_access.assert_called_once_with(self.MOCK_ALLOWED_USER, 'staff', moc_get_course_by_id.return_value)

    @patch('rg_instructor_analytics.views.log.error')
    @patch('rg_instructor_analytics.views.CourseKey.from_string')
    def test_enroll_statistic_post_call_with_fake_course(
            self,
            moc_course_key_from_string,
            moc_log_error,
    ):
        """
        Verify reaction to the invalid course
        """
        moc_course_key_from_string.return_value = 'key'
        moc_course_key_from_string.side_effect = Mock(side_effect=InvalidKeyError('', ''))

        request = self.factory.post('/courses/' + self.MOCK_COURSE_ID + '/tab/instructor_analytics/api/enroll_statics/')
        request.user = self.MOCK_ALLOWED_USER
        request.POST = self.MOCK_REQUEST_PARAMS

        response = EnrollmentStatisticView.as_view()(request, course_id=self.MOCK_COURSE_ID)

        self.assertEqual(response.status_code, 400)
        moc_log_error.assert_called_once_with(
            "Unable to find course with course key %s while getting enrollment statistic",
            self.MOCK_COURSE_ID
        )

    @patch('rg_instructor_analytics.views.log.error')
    @patch('rg_instructor_analytics.views.has_access')
    @patch('rg_instructor_analytics.views.get_course_by_id')
    @patch('rg_instructor_analytics.views.CourseKey.from_string')
    def test_enroll_statistic_post_call_with_unallowed_user(
            self,
            moc_course_key_from_string,
            moc_get_course_by_id,
            moc_has_access,
            moc_log_error
    ):
        """
        Verify reaction to user, which do not have access to  the given API
        """
        moc_course_key_from_string.return_value = 'key'
        moc_get_course_by_id.return_value = 'course'
        moc_has_access.return_value = False

        request = self.factory.post('/courses/' + self.MOCK_COURSE_ID + '/tab/instructor_analytics/api/enroll_statics/')
        request.user = self.MOCK_UN_ALLOWED_USER
        request.POST = self.MOCK_REQUEST_PARAMS

        response = EnrollmentStatisticView.as_view()(request, course_id=self.MOCK_COURSE_ID)

        moc_log_error.assert_called_once_with("Enrollment statistics not available for user type `%s`", request.user)
        self.assertEqual(response.status_code, 403)

    @patch('rg_instructor_analytics.views.EnrollmentStatisticView.get_state_before')
    @patch('rg_instructor_analytics.views.EnrollmentStatisticView.get_state_in_period')
    def test_get_statistic_per_day(self, mock_get_state_in_period, moc_get_state_before):
        moc_get_state_before.return_value = self.MOCK_PREVIOUS_ENROLL_STATE
        mock_get_state_in_period.return_value = self.MOCK_CURRENT_ENROLL_STATE
        stats = EnrollmentStatisticView.get_statistic_per_day(self.MOCK_FROM_DATE, self.MOCK_TO_DATE, 'key')

        self.assertEqual(stats, self.EXPECTED_ENROLL_STATISTIC)

    @patch('rg_instructor_analytics.views.EnrollmentStatisticView.request_to_db_for_stats_before')
    def test_get_state_before(self, mock_request_to_db_for_stats_before):
        """
        Verify getting statistics of the enrolled/unenrolled users before given day
        """
        mock_request_to_db_for_stats_before.return_value = [
            {'is_active': True, 'count': 10},
            {'is_active': False, 'count': 2},
        ]
        expect = (10, -2)
        stats = EnrollmentStatisticView.get_state_before('key', '12345')
        self.assertEqual(stats, expect)

        mock_request_to_db_for_stats_before.return_value = [
            {'is_active': False, 'count': 2},
        ]
        expect = (0, -2)
        stats = EnrollmentStatisticView.get_state_before('key', '12345')
        self.assertEqual(stats, expect)

        mock_request_to_db_for_stats_before.return_value = [
            {'is_active': True, 'count': 10},
        ]
        expect = (10, 0)
        stats = EnrollmentStatisticView.get_state_before('key', '12345')
        self.assertEqual(stats, expect)
