#!/usr/bin/env bash
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# Might be empty
cd /

CONFIG_FILE=/temp/airflow.cfg
SERVICE_ACCOUNT=/temp/service_account/*
WEBSERVER_CONFIG=/temp/config/webserver_config.py
AIRFLOW_CONNECTION=/temp/config/create-connection.sh

if [ -f "$CONFIG_FILE" ]; then
    cp /temp/airflow.cfg ${AIRFLOW_HOME}/airflow.cfg
    chown airflow:airflow ${AIRFLOW_HOME}/airflow.cfg
    echo "temp path: $(ls temp/)"
    echo "airflow path: $(ls ${AIRFLOW_HOME})"
fi

if [ -f "$WEBSERVER_CONFIG" ]; then
    cp /temp/config/webserver_config.py ${AIRFLOW_HOME}/webserver_config.py
    chown airflow:airflow ${AIRFLOW_HOME}/webserver_config.py
    echo "temp path: $(ls temp/)"
    echo "airflow path: $(ls ${AIRFLOW_HOME})"
fi

if [ -f "$AIRFLOW_CONNECTION" ]; then
    cp /temp/config/create-connection.sh ${AIRFLOW_HOME}/create-connection.sh
    chown airflow:airflow ${AIRFLOW_HOME}/create-connection.sh
    chmod 777 ${AIRFLOW_HOME}/create-connection.sh
    echo "temp path: $(ls temp/)"
    echo "airflow path: $(ls ${AIRFLOW_HOME})"
fi

if [ ${#SERVICE_ACCOUNT[@]} -gt 0 ]; then
    cp -R /temp/service_account/ ${AIRFLOW_HOME}/
    chown -R airflow:airflow ${AIRFLOW_HOME}/service_account
    echo "temp path: $(ls temp/)"
    echo "airflow path: $(ls ${AIRFLOW_HOME}/service_account)"
fi

cd ${AIRFLOW_HOME}

AIRFLOW_COMMAND="${1}"

set -euo pipefail

function verify_db_connection {
    DB_URL="${1}"

    DB_CHECK_MAX_COUNT=${MAX_DB_CHECK_COUNT:=20}
    DB_CHECK_SLEEP_TIME=${DB_CHECK_SLEEP_TIME:=3}

    local DETECTED_DB_BACKEND=""
    local DETECTED_DB_HOST=""
    local DETECTED_DB_PORT=""


    if [[ ${DB_URL} != sqlite* ]]; then
        # Auto-detect DB parameters
        [[ ${DB_URL} =~ ([^:]*)://([^@/]*)@?([^/:]*):?([0-9]*)/([^\?]*)\??(.*) ]] && \
            DETECTED_DB_BACKEND=${BASH_REMATCH[1]} &&
            # Not used USER match
            DETECTED_DB_HOST=${BASH_REMATCH[3]} &&
            DETECTED_DB_PORT=${BASH_REMATCH[4]} &&
            # Not used SCHEMA match
            # Not used PARAMS match

        echo DB_BACKEND="${DB_BACKEND:=${DETECTED_DB_BACKEND}}"

        if [[ -z "${DETECTED_DB_PORT}" ]]; then
            if [[ ${DB_BACKEND} == "postgres"* ]]; then
                DETECTED_DB_PORT=5432
            elif [[ ${DB_BACKEND} == "mysql"* ]]; then
                DETECTED_DB_PORT=3306
            fi
        fi

        DETECTED_DB_HOST=${DETECTED_DB_HOST:="localhost"}

        # Allow the DB parameters to be overridden by environment variable
        echo DB_HOST="${DB_HOST:=${DETECTED_DB_HOST}}"
        echo DB_PORT="${DB_PORT:=${DETECTED_DB_PORT}}"

        while true
        do
            set +e
            LAST_CHECK_RESULT=$(nc -zvv "${DB_HOST}" "${DB_PORT}" >/dev/null 2>&1)
            RES=$?
            set -e
            if [[ ${RES} == 0 ]]; then
                echo
                break
            else
                echo -n "."
                DB_CHECK_MAX_COUNT=$((DB_CHECK_MAX_COUNT-1))
            fi
            if [[ ${DB_CHECK_MAX_COUNT} == 0 ]]; then
                echo
                echo "ERROR! Maximum number of retries (${DB_CHECK_MAX_COUNT}) reached while checking ${DB_BACKEND} db. Exiting"
                echo
                break
            else
                sleep "${DB_CHECK_SLEEP_TIME}"
            fi
        done
        if [[ ${RES} != 0 ]]; then
            echo "        ERROR: ${DB_URL} db could not be reached!"
            echo
            echo "${LAST_CHECK_RESULT}"
            echo
            export EXIT_CODE=${RES}
        fi
    fi
}

if ! whoami &> /dev/null; then
  if [[ -w /etc/passwd ]]; then
    echo "${USER_NAME:-default}:x:$(id -u):0:${USER_NAME:-default} user:${AIRFLOW_USER_HOME_DIR}:/sbin/nologin" \
        >> /etc/passwd
  fi
  export HOME="${AIRFLOW_USER_HOME_DIR}"
fi


# if no DB configured - use sqlite db by default
AIRFLOW__CORE__SQL_ALCHEMY_CONN="${AIRFLOW__CORE__SQL_ALCHEMY_CONN:="sqlite:///${AIRFLOW_HOME}/airflow.db"}"

verify_db_connection "${AIRFLOW__CORE__SQL_ALCHEMY_CONN}"

AIRFLOW__CELERY__BROKER_URL=${AIRFLOW__CELERY__BROKER_URL:=}

if [[ -n ${AIRFLOW__CELERY__BROKER_URL} ]] && \
        [[ ${AIRFLOW_COMMAND} =~ ^(scheduler|worker|flower)$ ]]; then
    verify_db_connection "${AIRFLOW__CELERY__BROKER_URL}"
fi

if [[ ${AIRFLOW_COMMAND} == "bash" ]]; then
   shift
   exec "/bin/bash" "${@}"
elif [[ ${AIRFLOW_COMMAND} == "python" ]]; then
   shift
   exec "python" "${@}"
fi

airflow_home=/opt/airflow

cd ${airflow_home}

INITDB=${airflow_home}/airflow.db
if [ ! -f "$INITDB" ]; then
    airflow db init
fi

if [ ${1} == "scheduler" ]; then
    echo "success" > /opt/airflow/www/index.html
    # airflow "${@}" > /dev/null 2>&1 &
    exec python3 -m http.server -b 0.0.0.0 8999
    cat <<EOT > /etc/cron.d/scheduler-cron
PATH=/home/airflow/.local/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
*/4 * * * * cd /opt/airflow && airflow scheduler >> /var/log/scheduler.log 2>&1 
EOT
    chmod 0644 /etc/cron.d/scheduler-cron
    crontab /etc/cron.d/scheduler-cron
    touch /var/log/scheduler.log
    env >> /etc/environment
    cron
else
    # Run the command
    exec airflow "${@}"
fi

./create-connection.sh