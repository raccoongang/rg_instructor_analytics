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

VENDOR_CSS_URL = '{static_url}rg_instructor_analytics/css/vendor/scheduler/dhtmlxscheduler.css'.format(static_url=STATIC_URL)
VENDOR_JS_URL = '{static_url}rg_instructor_analytics/js/vendor/scheduler/_dhtmlxscheduler.js'.format(static_url=STATIC_URL)
VENDOR_PLUGIN_JS_URL = '{static_url}calendar_tab/js/vendor/scheduler/dhtmlxscheduler_readonly.js'.format(
    static_url=STATIC_URL
)
JS_URL = '{static_url}rg_instructor_analytics/js/rg_instructor_analytics.js'.format(static_url=STATIC_URL)


