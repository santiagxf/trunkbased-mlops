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

def get_model_version(subscription_id: str, resource_group: str, workspace_name:str,
                      model_name: str, version: str) -> str:
    cli_auth = AzureCliAuthentication()
    ws = aml.Workspace(subscription_id, resource_group, workspace_name, auth=cli_auth)

    model = get_model(ws, model_name, version)
    if model:
        return model.version
    else:
        return None

if __name__ == "__main__":
    tr = jobtools.runner.TaskRunner()
    result = tr.run(get_model_version)
    print(result)
    exit(0)