FROM apache/airflow:2.0.1

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3 \
        telnet \
        vim \
        libmysqlclient-dev \
        procps \
        cron

WORKDIR /
RUN mkdir -p temp/service_account \
    && mkdir -p opt/airflow/service_account \
    && mkdir -p opt/airflow/www \
    && chown -R airflow:airflow temp \
    && chown -R airflow:airflow opt \
    && chown -R airflow:airflow opt/airflow/www

COPY entrypoint.sh /entrypoint-init
RUN chmod a+x /entrypoint-init

WORKDIR /opt/airflow
COPY --chown=airflow:airflow src/main/python/requirements.txt ./
RUN pip install -r requirements.txt

EXPOSE 8080 5555 8793

USER airflow

WORKDIR /opt/airflow
RUN pip install --user -r requirements.txt

ENTRYPOINT ["/usr/bin/dumb-init", "--", "/entrypoint-init"]