"""
Model management capabilities from Azure ML
"""

import os
import logging
from typing import Any, List, Dict

import azureml.core as aml
from azureml.core.authentication import AzureCliAuthentication
from common.datasets.dataset_management import get_dataset

def download_model_from_context(model_name: str) -> os.PathLike:
    """
    Gets and downloads a given model from the model repository

    Parameters
    ----------
    model_name: str
        The name of the model
    
    Returns
    -------
    PathLike:
        The path to where the model content was downloaded.
    """
    workspace = aml.Run.get_context().experiment.workspace
    return workspace.models[model_name].download(exist_ok = True)


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

def register(ws_config: str, name: str, version: str, model_path: str,
             description: str, run_id: str = None, datasets_id: List[str] = None, tags: Dict[str, Any] = None):
    """
    Registers a model into the model registry using the given parameters. This method requires Azure CLI Authentication.
    """
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace.from_config(path=ws_config, auth=cli_auth)

    logging.warning(f"[WARN] Model version {version} parameter is only for backward compatibility. Latest is used.")

    if datasets_id:
        datasets = [get_dataset(worksapce=ws, name=ds) for ds in datasets_id]
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
            logging.error(f"[ERROR] Run with ID {run_id} couldn't been found. Model is not registered.")
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
        run = aml.Run.get(workspace=workspace, run_id=run_id)
    except Exception:
        run = None
    return run