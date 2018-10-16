"""
rg_instructor_analytics app.
"""
import logging
import os

from django.conf import settings
from path import Path

log = logging.getLogger(__name__)

APP_ROOT = Path(__file__).dirname()
ANALYTICS_TEMPLATE_DIR = os.path.join(APP_ROOT, 'templates')

try:
    settings.MAKO_TEMPLATES['main'].append(ANALYTICS_TEMPLATE_DIR)
    log.debug('MAKO_TEMPLATES["main"]: {}'.format(settings.MAKO_TEMPLATES['main']))
except AttributeError:
    settings.MAKO_TEMPLATE_DIRS_BASE.append(ANALYTICS_TEMPLATE_DIR)
    log.debug('MAKO_TEMPLATE_DIRS_BASE: {}'.format(settings.MAKO_TEMPLATE_DIRS_BASE))

