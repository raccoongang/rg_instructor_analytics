import logging

from django.conf import settings

from path import Path as path

log = logging.getLogger(__name__)

APP_ROOT = path(__file__).abspath().dirname()
STATIC_URL = settings.STATIC_URL

settings.MAKO_TEMPLATES['main'].extend([
    APP_ROOT / 'templates',
])
