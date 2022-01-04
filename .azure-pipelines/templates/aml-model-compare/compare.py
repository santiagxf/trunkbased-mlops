import logging
import argparse
import inspect
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

def compare(ws_config: str, model_name: str, champion: int, challenger: int, compare_by: str, greater_is_better: bool = True):
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
    ws = aml.Workspace.from_config(path=ws_config, auth=cli_auth)

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
    args = get_args_from_signature(compare)
    result = compare(**vars(args))
    exit(result)