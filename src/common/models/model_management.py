"""
Model management capabilities from Azure ML
"""

import os
import logging
from typing import Any, List, Dict

import azureml.core as aml
from azureml.exceptions import RunEnvironmentException, ModelNotFoundException
from azureml.core.authentication import AzureCliAuthentication
from common.datasets.dataset_management import get_dataset

def resolve_model_from_context(model_name: str, version: str = None, **tags) -> os.PathLike:
    """
    Resolves the name of a given model registered in Azure ML and downloads it in a local
    directory ready to be used. This method can resolve the model either when working inside
    of an Azure ML run or inside of an Azure ML compute.

    Parameters
    ----------
    model_name: str
        The name of the model to use. Model can also indicate the version in the format
        <model_name>:<model_version>. If so, `version` is ignored.
    version: str
        The version of the model. Version can be a number, a token like "latest" or a tag in
        the form <tag>=<tag_value>.
    """
    try:
        run = aml.Run.get_context(allow_offline=False)
        workspace = run.experiment.workspace
    except RunEnvironmentException:
        logging.warning("[WARN] Running outside of AML context. Trying to get workspace \
            from config.")
        workspace = aml.Workspace.from_config()

    model = get_model(workspace, model_name, version, **tags)
    if model:
        return model.download(exists_ok=True)
    else:
        return None

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
        return model
    except ModelNotFoundException:
        logging.warning("[WARN] Unable to find a model with the given specification")
        return None

def get_metric_for_model(workspace: aml.Workspace,
                         model_name: str,
                         version: int,
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
    version: int
        The version of the model
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
    model = aml.Model(workspace=workspace, name=model_name, version=version)
    if not model.run_id:
        raise ValueError(f"The model {model_name} has not a run associated with it. \
            Unable to retrieve metrics.")

    model_run = workspace.get_run(model.run_id)
    model_metric = model_run.get_metrics(name=metric_name)

    if metric_name not in model_metric.keys():
        raise ValueError(f"Metric with name {metric_name} is not present in \
            run {model.run_id} for model {model_name} ({model_hint}). Avalilable \
            metrics are {model_run.get_metrics().keys()}")

    return model_metric[metric_name]

def register(ws_config: str, name: str, version: str, model_path: str,
             description: str, run_id: str = None, datasets_id: List[str] = None,
             tags: Dict[str, Any] = None):
    """
    Registers a model into the model registry using the given parameters. This method
    requires Azure CLI Authentication.
    """
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace.from_config(path=ws_config, auth=cli_auth)

    logging.warning(f"[WARN] Model version {version} parameter is only for backward \
        compatibility. Latest is used.")

    if datasets_id:
        datasets = [get_dataset(workspace=ws, name=ds) for ds in datasets_id]
    else:
        datasets = None

    if run_id:
        logging.info(f"[INFO] Looking for run with ID {run_id}.")

        model_run = get_run(workspace=ws, run_id=run_id)
        if model_run:
            model_run.register_model(model_name=name,
                                     model_path=model_path,
                                     description=description,
                                     tags=tags,
                                     datasets=datasets)
        else:
            logging.error(f"[ERROR] Run with ID {run_id} couldn't been found. \
                Model is not registered.")
    else:
        aml.Model.register(workspace=ws,
                           model_name=name,
                           description=description,
                           model_path=model_path,
                           tags=tags,
                           datasets=datasets)

def get_run(workspace: aml.Workspace, run_id: str) -> aml.Run:
    """
    Gets a run from the workspace with a given ID.
    """
    try:
        run = aml.Run.get(workspace, run_id)
    except RuntimeError:
        run = None
    return run
