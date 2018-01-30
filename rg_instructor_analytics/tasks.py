"""
Module for celery tasks.
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from lms import CELERY_APP
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


@CELERY_APP.task
def send_email_to_cohort(subject, message, students):
    """
    Send email task.
    """
    context = {'subject': subject, 'body': message}
    html_content = render_to_string('rg_instructor_analytics/cohort_email_temolate.html', context)
    text_content = strip_tags(html_content)
    from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    msg = EmailMultiAlternatives(subject, text_content, from_address, students)
    msg.encoding = 'UTF-8'
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)
