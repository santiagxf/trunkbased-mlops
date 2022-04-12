import logging
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
            logging.info(f'[INFO] REmoving tag {tag}')
            model.remove_tags(tag)
    else:
        logging.error(f'[ERR] No model with name {name} and version {version}')
