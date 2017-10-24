import logging

from django.conf import settings

from path import Path as path

log = logging.getLogger(__name__)

APP_ROOT = path(__file__).abspath().dirname()
STATIC_URL = settings.STATIC_URL

settings.MAKO_TEMPLATES['main'].extend([
    APP_ROOT / 'templates',
])

log.debug('MAKO_TEMPLATES["main"]: {}'.format(settings.MAKO_TEMPLATES['main']))

JS_URL = '{static_url}rg_instructor_analytics/js/instructor_analytics.js'.format(static_url=STATIC_URL)
