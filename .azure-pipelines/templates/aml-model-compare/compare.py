import logging
import jobtools
import azureml.core as aml

from typing import Any
from azureml.core.authentication import AzureCliAuthentication
from azureml.exceptions import ModelNotFoundException, WebserviceException


def get_model(workspace: aml.Workspace, model_name: str, version: str = None, **tags) -> aml.Model:
    """
    Gets a model from the Azure Registry. `model_name` can be the name of the model,
    including it's version. use `[model_name]:[version]` or `[model_name]:latest` or
    `[model_name]:[tag]=[value]`

    Parameters
    ----------
    workspace: aml.Workspace
        Azure ML Workspace
    model_name: str
        Name of the model. It can include the model version.
    version: str
        Version of the model. If indicated in `model_name`, this parameter is ignored.
    tags: kwargs
        Tags the model should contain in order to be retrieved. If tags are indicated in
        model_name, this parameter is ignored.

    Return
    ------
    aml.Model
        The model if any
    """
    if ":" in model_name:
        stripped_model_name, version = model_name.split(':')
    else:
        stripped_model_name = model_name

    if version is None or version == "latest":
        model_version = None
    elif version == "current":
        raise ValueError("Model version 'current' is not support using this SDK right now.")
    elif '=' in version:
        model_tag_name, model_tag_value = version.split('=')
        model_version = None
        tags = { model_tag_name: model_tag_value }
    else:
        model_version = int(version)

    try:
        model = aml.Model(workspace=workspace,
                          name=stripped_model_name,
                          version=model_version,
                          tags=tags)
        
        if tags == None or (model.tags != None and set(tags.items()).issubset(model.tags.items())):
            # This is a bug in Model constructor. I won't filter correctly by tag.
            # Checking that manually.
            return model

    except ModelNotFoundException:
        logging.warning(f"[WARN] Unable to find a model with the given specification. \
            Name: {stripped_model_name}. Version: {model_version}. Tags: {tags}.")
    except WebserviceException:
        logging.warning(f"[WARN] Unable to find a model with the given specification. \
            Name: {stripped_model_name}. Version: {model_version}. Tags: {tags}.")
    
    logging.warning(f"[WARN] Unable to find a model with the given specification. \
            Name: {stripped_model_name}. Version: {model_version}. Tags: {tags}.")
    return None

def get_metric_for_model(workspace: aml.Workspace,
                         model_name: str,
                         version: str,
                         metric_name: str,
                         model_hint: str = None) -> Any:
    """
    Gets a given metric from the run that generated a given model and version.

    Parameters
    ----------
    workspace: azureml.core.Workspace
        The workspace where the model is stored.
    model_name: str
        The name of the model registered
    version: str
        The version of the model. It can be a number like "22" or a token like "latest" or a tag.
    metric_name: str
        The name of the metric you want to retrieve from the run
    model_hint: str | None
        Any hint you want to provide about the given version of the model. This is useful for
        debugging in case the given metric you indicated is not present in the run that generated
        the model.

    Return
    ------
        The value of the given metric if present. Otherwise an exception is raised.
    """
    model_run = get_run_for_model(workspace, model_name, version)
    model_metric = model_run.get_metrics(name=metric_name)

    if metric_name not in model_metric.keys():
        raise ValueError(f"Metric with name {metric_name} is not present in \
            run {model_run.id} for model {model_name} ({model_hint}). Avalilable \
            metrics are {model_run.get_metrics().keys()}")

    metric_value = model_metric[metric_name]

    if isinstance(metric_value, list):
        return metric_value[0]
    else:
        return metric_value

def get_run_for_model(workspace: aml.Workspace,
                      model_name: str, version: str = 'latest', **tags) -> aml.Run:
    """
    Gets a the run that generated a given model and version.

    Parameters
    ----------
    workspace: azureml.core.Workspace
        The workspace where the model is stored.
    model_name: str
        The name of the model registered
    version: str
        The version of the model. It can be a number like "22" or a token like "latest" or a tag.

    Return
    ------
        The given run.
    """
    model = get_model(workspace, model_name, version, **tags)
    if model:
        if not model.run_id:
            raise ValueError(f"The model {model_name} has not a run associated with it. \
                Unable to retrieve metrics.")

        return workspace.get_run(model.run_id)
    
    return None

def compare(subscription_id: str, resource_group: str, workspace_name:str, model_name: str,
            champion: str, challenger: str, compare_by: str, greater_is_better: bool = True):
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

    if not champion:
        logging.warning("[WARN] No champion model indicated. We infer there is no champion by the time.")
        return True

    champion_score = get_metric_for_model(ws, model_name, champion, compare_by, "champion")
    challenger_score = get_metric_for_model(ws, model_name, challenger, compare_by, "challenger")

    if champion_score and challenger_score:
        if greater_is_better:
            return champion_score < challenger_score
        else:
            return champion_score > challenger_score
    else:
        logging.warning("[WARN] No champion or challenger model indicated. We infer there is no champion by the time.")
        return True

if __name__ == "__main__":
    tr = jobtools.runner.TaskRunner()
    result = tr.run(compare)
    print(result)
    exit(0)