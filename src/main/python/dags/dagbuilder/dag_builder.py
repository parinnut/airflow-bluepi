from typing import Dict, Tuple, List
from airflow import DAG
from dagbuilder.utils import get_airflow_args, convert_function, convert_timedelta, to_bool, convert_datetime
from dagbuilder.operator_builder import build_operator

# Custom DAG arguments, only used for the program
CUSTOM_DAG_ARGS: Tuple[str, ...] = ("tasks", "flow",)


def prepare_dag_args(dag_args: Dict) -> Dict:
    for keypair in dag_args.items():
        key = keypair[0]
        val = keypair[1]

        if key == "default_args":
            tz = val.get("timezone")

            dag_args[key]['start_date'] = convert_datetime(val['start_date'], tz=tz)

            if dag_args[key].get('end_date'):
                dag_args[key]['end_date'] = convert_datetime(val['end_date'], tz=tz)

            if dag_args[key].get('retry_delay'):
                dag_args[key]['retry_delay'] = convert_timedelta(val['retry_delay'])
            
            if dag_args[key].get('max_retry_delay'):
                dag_args[key]['max_retry_delay'] = convert_timedelta(val['max_retry_delay'])

            if dag_args[key].get('sla'):
                dag_args[key]['sla'] = convert_timedelta(val['sla'])
                
            if dag_args[key].get('retry_exponential_backoff'):
                dag_args[key]['retry_exponential_backoff'] = to_bool(val['retry_exponential_backoff'])

        if key == "dagrun_timeout":
            dag_args[key] = convert_timedelta(val)

        if key in ["on_success_callback", "on_failure_callback", "sla_miss_callback"]:
            dag_args[key] = convert_function(val)

    return dag_args


def connect_tasks(tasks_map: Dict, op_dep_list: List) -> None:
    """
    :param tasks_map:       map of task inherited from airflow's own task
    :param op_dep_list:     list of dependencies between tasks

    for each item found in dep_list, set the next element of dep_list as its downstream.
    e.g. [[task1], [task2, task3]]    ->     task1.set_downstream([task2, task3])

    :return: nothing. but task's downstream attribute is modified.
    """
    if len(op_dep_list) == 0:
        return
    for index, op_list in enumerate(op_dep_list, 0):
        op_map = []
        try:
            for each_op in op_dep_list[index+1]:
                op_map.append(tasks_map[each_op])
            for task_name in op_list:
                tasks_map[task_name].set_downstream(op_map)
        except IndexError:
            continue


def build_dag(config: Dict) -> DAG:
    dag_args = prepare_dag_args(get_airflow_args(config, CUSTOM_DAG_ARGS))
    dag = DAG(**dag_args)

    tasks_map = {}
    dependency_master_list = []

    flow = config.get('flow')

    if flow:
        for each_line in flow:
            task_dependencies = convert_flow_into_dependency_list(each_line)
            dependency_master_list.append(task_dependencies)

    for task_config in config['tasks']:
        op = build_operator(task_config, dag)
        tasks_map[op.task_id] = op

    for task_dependencies in dependency_master_list:
        connect_tasks(tasks_map, task_dependencies)

    return dag


def convert_flow_into_dependency_list(flow: str) -> List:
    """
    :param flow:

    flow example:               'task1 >> [task2, task3] >> task4'
    converts into dep_list:     [['task1'], ['task2', 'task3'], ['task4']]

    :return: dependency_list
    """
    flow_as_list = flow.replace(' ', '').split('>>')
    dependency_list = []
    for each_item in flow_as_list:
        dependency_list.append(each_item.strip('][').split(','))
    return dependency_list
