"""
Model management capabilities from Azure ML
"""

import os
from azureml.core import Run

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
    workspace = Run.get_context().experiment.workspace
    return workspace.models[model_name].download(exist_ok = True)
