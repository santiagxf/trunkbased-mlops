import logging
import azureml.core as aml

from typing import List, Dict, Any
from azureml.core.authentication import AzureCliAuthentication

def get_dataset(workspace: aml.Workspace, name: str) -> aml.Dataset:
    """
    Gets a dataset from the workspace with a given name
    """
    try:
        dataset = aml.Dataset.get_by_name(
            workspace=workspace,
            name=name,
            version="latest"
        )
    except Exception:
        dataset = None
    return dataset

def get_run(workspace: aml.Workspace, run_id: str) -> aml.Run:
    """
    Gets a run from the workspace with a given ID.
    """
    try:
        run = aml.Run.get(workspace=workspace, run_id=run_id)
    except Exception:
        run = None
    return run

def register(subscription_id: str, resource_group: str, workspace_name:str, name: str, version: str, model_path: str,
             description: str, run_id: str = None, datasets_id: List[str] = None, tags: Dict[str, Any] = None):
    """
    Registers a model into the model registry using the given parameters. This method requires Azure CLI Authentication.
    """
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace(subscription_id, resource_group, workspace_name, auth=cli_auth)

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
