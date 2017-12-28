# rg_instructor_analytics

## Unit tests
All tests could be run only in local. 
##### For run unit test follow the next steps:
* Ensure that the source placed in one of the edx-platform subdirectory.
* cd rg_instructor_analytics
* sh ./test_tool/run_test.sh

## For collect static:
```bash
ssh ubuntu@edx-staging-rg-instructor-analytics.raccoongang.com
sudo -Hu edxapp bash;
source /edx/app/edxapp/edxapp_env
cd /edx/app/edxapp/edx-platform
python ./manage.py lms collectstatic --settings=$EDX_PLATFORM_SETTINGS --noinput
sudo /edx/bin/supervisorctl restart edxapp:lms
```
