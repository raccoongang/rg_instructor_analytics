# rg_instructor_analytics

## Installation
* Add `rg_instructor_analytics` to the installed app 
* Add to lms url: 
```python
url(
        r'^courses/{}/tab/instructor_analytics/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        include('rg_instructor_analytics.urls'),
        name='instructor_analytics_endpoint',
    ),
```
* Add in to the settings file: 
```python
FEATURES['ENABLE_XBLOCK_VIEW_ENDPOINT'] = True
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
