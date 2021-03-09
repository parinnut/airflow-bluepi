import importlib
import re
from typing import Callable, List, Dict, Tuple
from datetime import timedelta, datetime, date
import copy
import yaml
import dateparser
import pendulum
import glob

from constants import Timezone

try:
    from yaml import CSafeLoader as SafeLoader, CSafeDumper as SafeDumper
except ImportError:
    from yaml import SafeLoader, SafeDumper

TIME_UNITS = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}
CONFIG_FILE_EXT = '.yaml'


def list_config_files(dir_path: str) -> List:
    dir_to_scan = dir_path if dir_path.endswith('/') else dir_path + '/'
    return glob.glob(dir_to_scan + '**/*' + CONFIG_FILE_EXT, recursive=True)


def read_config(config_file: str) -> Dict:
    with open(config_file, 'r') as file:
        return yaml.load(file, Loader=yaml.SafeLoader)


def get_airflow_args(config: Dict, exclude_keys: Tuple) -> Dict:
    cfg = copy.deepcopy(config)
    for arg in exclude_keys:
        try:
            del cfg[arg]
        except KeyError:
            continue
    return cfg


"""
parameter conversion functions
"""


def convert_function(fn_package: str) -> Callable:
    module = importlib.import_module(fn_package)
    return module.main


def convert_datetime(dt: [str, datetime, date], tz: str) -> pendulum.datetime:
    if tz is None:
        tz = Timezone.UTC

    timezone_local = pendulum.timezone(tz)
    timezone_utc = pendulum.timezone(Timezone.UTC)

    if type(dt) is str:
        parsed_datetime = dateparser.parse(dt)

        if parsed_datetime is None:
            raise ValueError("\"{}\" cannot be parsed to datetime".format(type(dt)))

        parsed_datetime = parsed_datetime.replace(tzinfo=timezone_utc)
        return pendulum.instance(parsed_datetime.astimezone(timezone_local)).replace(tzinfo=timezone_local)
    elif type(dt) is datetime:
        dt = dt.replace(tzinfo=timezone_utc)
        return pendulum.instance(dt.astimezone(timezone_local)).replace(tzinfo=timezone_local)
    elif type(dt) is date:
        dt = datetime(dt.year, dt.month, dt.day, 0, 0, 0, tzinfo=timezone_utc)
        return pendulum.instance(dt.astimezone(timezone_local)).replace(tzinfo=timezone_local)

    raise TypeError(
        "Cannot convert data type \"{}\" to pendulum.datetime. Only support str, datetime, date".format(type(dt))
    )


def convert_timedelta(time_duration: str) -> timedelta:
    matched_durations = re.finditer(r'(?P<val>\d+)(?P<unit>[smhdw]?)', time_duration, flags=re.I)
    return timedelta(**{
        TIME_UNITS.get(m.group('unit').lower(), 'seconds'): int(m.group('val')) for m in matched_durations
    })

def to_bool(value: str) -> bool:
    valid = {'true': True, 't': True, '1': True,
             'false': False, 'f': False, '0': False}

    if isinstance(value, bool):
        return value

    lower_value = str(value).lower()
    if lower_value in valid:
        return valid[lower_value]
    else:
        raise ValueError(f'invalid literal for boolean ({value})')
