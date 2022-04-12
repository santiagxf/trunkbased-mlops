import logging
import mlflow
import azureml.core as aml
from azureml.core.authentication import AzureCliAuthentication

def add_tag(subscription_id: str, resource_group: str, workspace_name:str, name: str, version: str, tag: str, value: str):
    """
    Adds a tag to a given model
    """
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace(subscription_id, resource_group, workspace_name, auth=cli_auth)

    model = aml.Model(ws, name=name, version=version)
    if model:
        logging.info(f'[INFO] Adding tag {tag} with value {value}')
        model.add_tags({ tag: value})
    else:
        logging.error(f'[ERR] No model with name {name} and version {version}')

def remove_tag(subscription_id: str, resource_group: str, workspace_name:str, name: str, version: str, tag: str):
    """
    Removes a tag to a given model
    """
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace(subscription_id, resource_group, workspace_name, auth=cli_auth)

    model = aml.Model(ws, name=name, version=version)
    if model:
        if tag in model.tags.keys():
            logging.info(f'[INFO] Removing tag {tag}')
            model.remove_tags(tag)
    else:
        logging.error(f'[ERR] No model with name {name} and version {version}')


def update_model_stage(subscription_id: str, resource_group: str, workspace_name:str, name: str, version: str, stage: str, archiveExisting: bool = True):
    """
    Updates the MLflow model's stage
    """

    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace(subscription_id, resource_group, workspace_name, auth=cli_auth)
    client = mlflow.tracking.MlflowClient(ws.get_mlflow_tracking_uri())
    mlflow_stage = stage.capitalize()
    if mlflow_stage in client.get_model_version_stages(name=name, version=version):
        client.transition_model_version_stage(name=name, version=version, stage=mlflow_stage, archive_existing_versions=archiveExisting)
    else:
        logging.error(f'[ERR] Stage {mlflow_stage} is not valid for model {name}:{version}')
