import importlib

from typing import Dict, Tuple, Type
from airflow import DAG
from airflow.models import BaseOperator

from dagbuilder.utils import get_airflow_args, convert_function, convert_timedelta

# Custom operator arguments, only used for the program
CUSTOM_OPERATOR_ARGS: Tuple[str, ...] = ("operator", "dependencies",)


def build_operator(config: Dict, dag: DAG) -> Type[BaseOperator]:
    operator_name = config['operator']
    last_dot_index = operator_name.rindex('.')
    op_module = operator_name[0: last_dot_index]
    op_class = operator_name[last_dot_index + 1:]
    operator = getattr(importlib.import_module(op_module), op_class)
    op_args = get_airflow_args(config, CUSTOM_OPERATOR_ARGS)

    return operator(dag=dag, **op_args)
