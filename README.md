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
* Add in to the settings file (i.e. in `edx-platform/lms/envs/common.py`): 
```python
FEATURES['ENABLE_XBLOCK_VIEW_ENDPOINT'] = True

INSTALLED_APPS += ('rg_instructor_analytics',)
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
    "RG_ANALYTICS_ENROLLMENT_STAT_UPDATE":{
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


## Unit tests
All tests could be run only in local. 
##### For run unit test follow the next steps:
* Ensure that the source placed in one of the edx-platform subdirectory.
* cd rg_instructor_analytics
* sh ./test_tool/run_test.sh

