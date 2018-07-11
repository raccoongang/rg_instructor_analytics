"""
Manage.py command for pre-collecting analytics data.
"""
from django.core.management.base import BaseCommand

from rg_instructor_analytics.tasks import run_common_static_collection


class Command(BaseCommand):
    """
    Command for initial collecting data for the rg_instructor_analytics.
    """

    help = """
    Run Celery task to collect data required for analytics.

    Attention - the first run of the collecting data may take several hours.
    """

    def handle(self, *args, **options):
        """
        Handle command.
        """
        run_common_static_collection.delay()
