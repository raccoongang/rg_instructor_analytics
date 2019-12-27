# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import os
from path import Path

from django.apps import AppConfig
from openedx.core.constants import COURSE_ID_PATTERN
from openedx.core.djangoapps.plugins.constants import ProjectType, PluginURLs


log = logging.getLogger(__name__)


class InstructorAnalyticsConfig(AppConfig):
    name = 'rg_instructor_analytics'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: u'rg_instructor_analytics',
                PluginURLs.APP_NAME: u'rg_instructor_analytics',
                PluginURLs.REGEX: r'^courses/{}/customtab/instructor_analytics/'.format(
                    COURSE_ID_PATTERN
                ),
            }
        },
    }

    def ready(self):
        from django.conf import settings
        from edxmako import add_lookup

        # This import need for register tasks in celery
        from .tasks import *

        APP_ROOT = Path(__file__).dirname()
        ANALYTICS_TEMPLATE_DIR = os.path.join(APP_ROOT, 'templates')

        settings.MAKO_TEMPLATE_DIRS_BASE.append(ANALYTICS_TEMPLATE_DIR)
        log.debug('MAKO_TEMPLATE_DIRS_BASE: {}'.format(settings.MAKO_TEMPLATE_DIRS_BASE))

        for t in settings.TEMPLATES:
            if t.get('NAME') == 'mako':
                namespace = t['OPTIONS'].get('namespace', 'main')
                add_lookup(namespace, ANALYTICS_TEMPLATE_DIR)
