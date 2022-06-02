import logging
import mlflow
import azureml.core as aml
from azureml.core.authentication import AzureCliAuthentication
from azureml.exceptions import RunEnvironmentException, ModelNotFoundException, WebserviceException

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
    tags_list = None

    if ":" in model_name:
        stripped_model_name, version = model_name.split(':')
    else:
        stripped_model_name = model_name

    if version is None or version == "latest":
        model_version = None
    elif version == "current":
        raise ValueError("Model version 'current' is not support using this SDK right now.")
    elif '=' in version:
        model_version = None
        tags_list = [ version ]
    else:
        model_version = int(version)

    if tags:
        if tags_list:
            logging.warning("[WARN] Indicating tags both in version and tags keywords is not supported. Tags are superseded by version.")
        else:
            tags_list = [ f'{tag[0]}={tag[1]}' for tag in tags.items() ]

    try:
        model = aml.Model(workspace=workspace,
                          name=stripped_model_name,
                          version=model_version,
                          tags=tags_list)

        if model:
            logging.info(f"[INFO] Returning model with name: {model.name}, version: {model.version}, tags: {model.tags}")

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

def add_tag(subscription_id: str, resource_group: str, workspace_name:str, name: str, version: str, tag: str, value: str):
    """
    Adds a tag to a given model
    """
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace(subscription_id, resource_group, workspace_name, auth=cli_auth)

    model = get_model(ws, model_name=name, version=version)
    if model:
        logging.info(f'[INFO] Adding tag {tag} with value {value}')
        model.add_tags({ tag: value})
    else:
        logging.info(f'[INFO] No model with name {name} and version {version} matching. No tags has been updated.')

def remove_tag(subscription_id: str, resource_group: str, workspace_name:str, name: str, version: str, tag: str):
    """
    Removes a tag to a given model
    """
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace(subscription_id, resource_group, workspace_name, auth=cli_auth)

    model = get_model(ws, model_name=name, version=version)
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
