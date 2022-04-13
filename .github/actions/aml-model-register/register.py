import os
import logging
import mlflow
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

def register(subscription_id: str, resource_group: str, workspace_name:str, name: str, model_path: str,
             description: str, run_id: str = None, datasets_id: List[str] = None, tags: Dict[str, Any] = None):
    """
    Registers a model into the model registry using the given parameters. This method requires Azure CLI Authentication.
    """
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace(subscription_id, resource_group, workspace_name, auth=cli_auth)

    if datasets_id:
        datasets = [get_dataset(worksapce=ws, name=ds) for ds in datasets_id]
    else:
        datasets = None

    if run_id:
        logging.info(f"[INFO] Logging with MLflow {run_id}.")

        mlflow_tracking_uri = f'azureml://eastus2.api.azureml.ms/mlflow/v1.0/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.MachineLearningServices/workspaces/{workspace_name}'
        os.environ['MLFLOW_TRACKING_URI'] = mlflow_tracking_uri
        mlflow.set_registry_uri(mlflow_tracking_uri)
        mlflow.register_model(f'runs:/{run_id}/{model_path}', name)
    else:
        aml.Model.register(workspace=ws, 
                           model_name=name,
                           description=description,
                           model_path=model_path, 
                           tags=tags,
                           datasets=datasets)
