"""
rg_instructor_analytics app.
"""
import logging

from django.conf import settings
from path import Path as path

log = logging.getLogger(__name__)

APP_ROOT = path(__file__).abspath().dirname()

settings.MAKO_TEMPLATES['main'].extend([
    APP_ROOT / 'templates',
])

log.debug('MAKO_TEMPLATES["main"]: {}'.format(settings.MAKO_TEMPLATES['main']))
