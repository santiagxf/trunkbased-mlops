import jobtools
import azureml.core as aml

from typing import Any
from azureml.core.authentication import AzureCliAuthentication

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

def assert_metric(subscription_id: str, resource_group: str, workspace_name:str, job_name: str,
                  metric: str, expected: str, data_type: str, greater_is_better: bool = True) -> bool:
    """
    Asserts that a given metric in a job has the expected value.

    Parameters
    ----------
    subscription_id: str
        The subscription id where the workspace is located.
    resource_group: str
        The resource group where the workspace is located.
    workspace_name: str
        Workspace name
    job_name: str
        The unique job name (aka run id) that logged the metric.
    metric: str
        Name of a metric logged in the run/job.
    expected: str
        Value that you are expecting the metric to have. The value would be cast to `data_type`.
    data_type: str
        Type of the value in `expected`. Possible values are [`boolean`, `bool`, `numeric`, `int`, `integer`, `string`, `str`]
    greater_is_better: bool
        Indicates if greater values that the indicated at `expected` are better. Only for types `numeric`, `int`, `integer` and `float`.

    Return
    ------
    bool:
        If the assertion is satisfied.
    """
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace(subscription_id, resource_group, workspace_name, auth=cli_auth)

    metric_value = get_metric_for_job(ws, job_name, metric)

    if data_type in ["boolean", "bool"]:
        return bool(metric_value)

    if data_type in ["float", "numeric", "int", "integer"]:
        return float(metric_value) > float(expected) if greater_is_better else float(metric_value) < float(expected)

    return ValueError(f"Data type {data_type} is not supported")


if __name__ == "__main__":
    tr = jobtools.runner.TaskRunner()
    result = tr.run(assert_metric)
    exit(result)
