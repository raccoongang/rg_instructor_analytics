#!/bin/bash

#all test running in ex's runtime

PROJECT_ROOT=$(pwd)
export SERVICE_VARIANT="lms"
export DISABLE_MIGRATIONS="false"
cd ~/edx-platform/

MYSQL=$(which mysql)
GRANT_REQUEST1="GRANT ALL PRIVILEGES ON test_edxapp.* TO 'edxapp001'@'localhost'"
GRANT_REQUEST2="GRANT ALL PRIVILEGES ON test_edxapp.* TO 'migrate'@'localhost'"
GRANT_REQUEST3="GRANT ALL PRIVILEGES ON test_edxapp_csmh.* TO 'edxapp001'@'localhost'"
GRANT_REQUEST4="GRANT ALL PRIVILEGES ON test_edxapp_csmh.* TO 'migrate'@'localhost'"
$MYSQL -u root mysql -e "$GRANT_REQUEST1"
$MYSQL -u root mysql -e "$GRANT_REQUEST2"
$MYSQL -u root mysql -e "$GRANT_REQUEST3"
$MYSQL -u root mysql -e "$GRANT_REQUEST4"

pytest $PROJECT_ROOT/../tests -c $PROJECT_ROOT/../pytest.ini
