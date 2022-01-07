"""
A module to facilitate the use of Azure ML datasets.
"""
import azureml.core as aml

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
    except RuntimeError:
        dataset = None
    return dataset
