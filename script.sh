#set up virtual box
https://www.virtualbox.org/wiki/Downloads
#install airflow
sh install-airflow.sh
airflow db init

#start webserver
airflow webserver

#start scheduler

#create user
airflow users create -u admin -p admin -f Parin -l Lou -r Admin -e admin@airflow.com

#list dag
airflow dags list
#list task
airflow tasks list example_xcom_args


airflow dags trigger -e 2020-01-01 example_xcom_args

#stop airflow
systemctl stop airflow

#summit connector
#spark-submit --jars=bigquery-connector-hadoop2-latest.jar --class  com.google.cloud.hadoop.io.bigquery.JsonTextBigQueryInputFormat /home/jupyter/bluepi_exam.ipynb

#running steps
#after start airflow
#create postgres connection
#create google cloud connection