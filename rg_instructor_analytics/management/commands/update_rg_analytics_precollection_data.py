"""
Manage.py command for the update precollected data.
"""
from django.core.management.base import BaseCommand

from rg_instructor_analytics.tasks import run_common_static_collection


class Command(BaseCommand):
    """
    Command for initial collect data for the rg_instructor_analytics.
    """

    help = """
    Send task to celery for update internal data about platform.

    Attention - collection of the initial data take several hours.
    """

    def handle(self, *args, **options):
        """
        Handle command.
        """
        run_common_static_collection.delay()
