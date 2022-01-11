import logging
import argparse
import inspect
from azureml import data
import azureml.core as aml

from os import PathLike
from typing import Dict, Any, List, Callable, Union
from azureml.core import workspace
from azureml.core.authentication import AzureCliAuthentication

def get_args_from_signature(method: Callable) -> argparse.Namespace:
    """
    Automatically parses all the arguments to match an specific method. The method should implement type hinting in order for this to work.
    All arguments required by the method will be also required by the parser. To match bash conventions, arguments with underscore will be
    parsed as arguments with upperscore. For instance `from_path` will be requested as `--from-path`.

    Parameters
    ----------
    method: Callable
        The method the arguments should be extracted from.

    Returns
    -------
    argparse.Namespace
        The arguments parsed. You can call `method` with `**vars(...)` then
    """
    parser = argparse.ArgumentParser()
    fullargs = inspect.getfullargspec(method)
    num_args_with_defaults = 0 if fullargs.defaults == None else len(fullargs.defaults)
    required_args_idxs = len(fullargs.annotations) - num_args_with_defaults
    for idx, (arg, arg_type) in enumerate(fullargs.annotations.items()):
        is_required = idx < required_args_idxs
        parser.add_argument(f"--{arg.replace('_','-')}", dest=arg, type=arg_type, required=is_required)

    return parser.parse_args()

def get_metric_for_job(workspace: aml.Workspace, job_name: str, metric_name: str) -> Any:
    """
    Gets a given metric from a job run

    Parameters
    ----------
    workspace: azureml.core.Workspace
        The workspace where the model is stored.
    job_name: str
        The name of the job
    metric_name: str
        The name of the metric you want to retrieve from the run

    Return
    ------
        The value of the given metric if present. Otherwise an exception is raised.
    """
    job_run = workspace.get_run(job_name)
    job_metric = job_run.get_metrics(name=metric_name)

    if metric_name not in job_metric.keys():
        raise ValueError(f"Metric with name {metric_name} is not present in job {job_name}. Avalilable metrics are {job_run.get_metrics().keys()}")

    return job_metric[metric_name]

def assert_metric(ws_config: str, job_name: str, metric: str, expected: str, data_type: str, greater_is_better: bool = True):
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace.from_config(path=ws_config, auth=cli_auth)

    metric_value = get_metric_for_job(ws, job_name, metric)

    if data_type in ["boolean", "bool"]:
        return bool(metric_value)

    if data_type in ["float", "numeric", "int", "integer"]:
        return float(metric_value) > float(expected) if greater_is_better else float(metric_value) < float(expected)

    return ValueError(f"Data type {data_type} is not supported")


if __name__ == "__main__":
    args = get_args_from_signature(assert_metric)
    result = assert_metric(**vars(args))
    exit(result)