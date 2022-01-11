import logging
import argparse
import inspect
import azureml.core as aml

from os import PathLike
from typing import Dict, Any, List, Callable, Union
from azureml.core.authentication import AzureCliAuthentication

def get_args_from_signature(method: Callable) -> argparse.Namespace:
    """
    Automatically parses all the arguments to match an specific method. The method should implement type hinting in order for this to work.
    All arguments required by the method will be also required by the parser. To match bash conventions, arguments with underscore will be
    parsed as arguments with upperscore. For instance `from_path` will be requested as `--from-path`.

    Parameters
    ----------
    method: Callable
        The method the arguments should be extracted from.

    Returns
    -------
    argparse.Namespace
        The arguments parsed. You can call `method` with `**vars(...)` then
    """
    parser = argparse.ArgumentParser()
    fullargs = inspect.getfullargspec(method)
    num_args_with_defaults = 0 if fullargs.defaults == None else len(fullargs.defaults)
    required_args_idxs = len(fullargs.annotations) - num_args_with_defaults
    for idx, (arg, arg_type) in enumerate(fullargs.annotations.items()):
        is_required = idx < required_args_idxs
        parser.add_argument(f"--{arg.replace('_','-')}", dest=arg, type=arg_type, required=is_required)

    return parser.parse_args()

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

if __name__ == "__main__":
    args = get_args_from_signature(register)
    register(**vars(args))