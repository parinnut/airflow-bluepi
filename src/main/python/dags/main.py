import os
from airflow import DAG, AirflowException
from dagbuilder.dag_builder import build_dag
from dagbuilder.utils import read_config, list_config_files


# airflow_home = os.environ.get("AIRFLOW_HOME")
# airflow_dags_config_path = os.environ.get("AIRFLOW_CONFIG_PATH")
# if airflow_dags_config_path:
#     config_default_path = airflow_dags_config_path
# elif not airflow_dags_config_path:
#     config_default_path = "dags/config"

airflow_home = os.environ.get("AIRFLOW_HOME")

project_id = os.environ.get("GOOGLE_PROJECT_ID")

if not project_id:
    config_default_path = f"dags/config/local"
else:
    config_default_path = f"dags/sync/src/main/python/dags/config/{project_id}"

config_dir = os.path.join(airflow_home, str(config_default_path))
config_files = list_config_files(config_dir)

print(f'config_default_path: {config_default_path}')
print(f'config_dir: {config_dir}')

config_errors = []

for config_file in config_files:
    print(f'found config : {config_file}')
    try:
        config = read_config(config_file)
        dag: DAG = build_dag(config)

        # register dag to airflow
        globals()[dag.dag_id] = dag
    except Exception as e:
        error_config_file = config_file.replace(config_dir, '')
        config_errors.append(f'config: {error_config_file}, reason: {e}')


if config_errors:
    raise AirflowException("\n".join(config_errors))
