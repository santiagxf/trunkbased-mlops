import logging
import jobtools
import azureml.core as aml

from typing import Any
from azureml.core import workspace
from azureml.core.authentication import AzureCliAuthentication


def get_metric_for_model(workspace: aml.Workspace, model_name: str, version: int, metric_name: str, model_hint: str = None) -> Any:
    """
    Gets a given metric from the run that generated a given model and version.

    Parameters
    ----------
    workspace: azureml.core.Workspace
        The workspace where the model is stored.
    model_name: str
        The name of the model registered
    version: int
        The version of the model
    metric_name: str
        The name of the metric you want to retrieve from the run
    model_hint: str | None
        Any hint you want to provide about the given version of the model. This is useful for debugging in case the given
        metric you indicated is not present in the run that generated the model.

    Return
    ------
        The value of the given metric if present. Otherwise an exception is raised.
    """
    model = aml.Model(workspace=workspace, name=model_name, version=version)
    if not model.run_id:
        raise ValueError(f"The model {model_name} has not a run associated with it. Unable to retrieve metrics.")

    model_run = workspace.get_run(model.run_id)
    model_metric = model_run.get_metrics(name=metric_name)

    if metric_name not in model_metric.keys():
        raise ValueError(f"Metric with name {metric_name} is not present in run {model.run_id} for model {model_name} ({model_hint}). Avalilable metrics are {model_run.get_metrics().keys()}")

    return model_metric[metric_name]

def compare(subscription_id: str, resource_group: str, workspace_name:str, model_name: str,
            champion: int, challenger: int, compare_by: str, greater_is_better: bool = True):
    """
    Compares a challenger model version with a champion one and indicates if the new version (challenger) is
    better than the current one (champion) while comparing them using `compared_by`. Metrics are retrieved
    from the associated runs that generated each of the models versions.

    Parameters
    ----------
    ws_config: PathLike
        The path to the workspace configuration file.
    model_name: str
        The name of the model to compare
    champion: int
        The version number of a registered model acting as the champion
    challenger: int
        The version number of a registered model acting as the challenger
    compared_by: str
        The name of a metric present in the runs that generated both challenger and champion
    greater_is_better: bool
        Indicates if greater valuer is the metric are better
    """
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace(subscription_id, resource_group, workspace_name, auth=cli_auth)

    if champion == 0:
        logging.warning("[WARN] No champion model indicated. We infer there is no champion by the time.")
        return True

    champion_score = get_metric_for_model(ws, model_name, champion, compare_by, "champion")
    challenger_score = get_metric_for_model(ws, model_name, challenger, compare_by, "challenger")

    if greater_is_better:
        return champion_score < challenger_score
    else:
        return champion_score > challenger_score

if __name__ == "__main__":
    tr = jobtools.runner.TaskRunner()
    result = tr.run(compare)
    print(result)
    exit(0)