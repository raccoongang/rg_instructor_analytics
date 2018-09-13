# rg_instructor_analytics

## Installation
* Add `rg_instructor_analytics` and `web_fragments` to the INSTALLED_APPS (i.e. in `edx-platform/lms/envs/common.py`)
* Add to lms url (i.e. in `edx-platform/lms/urls.py`): 
```python
url(
        r'^courses/{}/tab/instructor_analytics/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        include('rg_instructor_analytics.urls'),
        name='instructor_analytics_endpoint',
    ),
```
> Note: url definition must be *before* url with name `course_tab_view`
* Add in to the settings file (i.e. in `edx-platform/lms/envs/common.py`): 
```python
FEATURES['ENABLE_XBLOCK_VIEW_ENDPOINT'] = True

FEATURES['ENABLE_RG_INSTRUCTOR_ANALYTICS'] = True

INSTALLED_APPS += ('rg_instructor_analytics', 'web_fragments',)
```
* Apply migration
* Ensure that celerybeat is running
* Set setting for enrollment cache update, for example:
    * for common.py
    ```python
    RG_ANALYTICS_ENROLLMENT_STAT_UPDATE = {
        'minute': '*',
        'hour': '*/6',
        'day_of_week': '*',
        'day_of_month': '*',
        'month_of_year': '*',
    }
    ```
    * for json config:

    ```json
    "RG_ANALYTICS_ENROLLMENT_STAT_UPDATE": {
        "minute": "*",
        "hour": "*/6",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*"
    }
    ```
* Set setting for grade cache update, for example:
    * for common.py
    ```python
    RG_ANALYTICS_GRADE_STAT_UPDATE = {
        'minute': '*',
        'hour': '*/6',
        'day_of_week': '*',
        'day_of_month': '*',
        'month_of_year': '*',
    }
    ```
    * for json config:

    ```json
    "RG_ANALYTICS_GRADE_STAT_UPDATE": {
        "minute": "*",
        "hour": "*/6",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*"
    }
    ```
* Run in the console:
```bash
sudo -sHu edxapp
cd 
. edxapp_env
pip install -e git+https://github.com/raccoongang/rg_instructor_analytics@master#egg=rg_instructor_analytics
cd edx-platform
python ./manage.py lms collectstatic --settings=$EDX_PLATFORM_SETTINGS --noinput
exit
sudo /edx/bin/supervisorctl restart edxapp:lms
```

##### After installation run next code in Django shell (warning this tasks can take time) 
```python
from rg_instructor_analytics.tasks import enrollment_collector_date, grade_collector_stat 

grade_collector_stat()
enrollment_collector_date()
```

## Microsites 

for microsite configurations use this flag for enable/disable tab: `ENABLE_RG_INSTRUCTOR_ANALYTICS`

## Unit tests
All tests could be run only in local. 
##### For run unit test follow the next steps:
* Ensure that the source placed in one of the edx-platform subdirectory.
* cd rg_instructor_analytics
* sh ./test_tool/run_test.sh

