"""
Scoring routines for models based on transformers.
"""
import logging
import json
import os
from typing import List, Union

import pandas as pd
import numpy as np
import mlflow
from inference_schema.schema_decorators import input_schema, output_schema
from inference_schema.parameter_types.numpy_parameter_type import NumpyParameterType
from inference_schema.parameter_types.pandas_parameter_type import PandasParameterType


try:
    from azureml.core import Workspace
except ImportError:
    logging.info("[INFO] from_workspace argument for the init method is not enabled")

# Sample input for the service
input_sample = pd.DataFrame(data=[{
    "text": "este é o texto amostral"
}])

# Sample output for the service
output_sample = np.array([0.1, 0.1])

MODEL = None

def init(from_workspace: bool = False, workspace = None):
    """
    Initialization routine for the model

    Parameters
    ----------
    from_workspace: bool
        Indicates if model will be loaded from an AML workspace
    workspace: azureml.core.Workspace
        The workspace to load the model from. Only used if `from_workspace` is true.
        If not indicated, it will try to load it with method `from_config`. This will
        only work inside of an Azure ML compute.
    """
    global MODEL

    model_name = 'hate-pt-speech'

    if not from_workspace:
        model_path = os.getenv("AZUREML_MODEL_DIR")
        model_package = f'{model_path}/{model_name}'
    else:
        logging.warning("[WARN] Opening model from workspace")

        if workspace is None:
            logging.warning("[WARN] Looking for configuration in current compute")
            workspace = Workspace.from_config()
        model_package = workspace.models[model_name].download(exist_ok = True)

    logging.info(f"[INFO] Loading model from package {model_package}")

    MODEL = mlflow.pyfunc.load(model_package)

    logging.info("[INFO] Init completed")

@input_schema('raw_data', PandasParameterType(input_sample))
@output_schema(NumpyParameterType(output_sample))
def run(raw_data: Union[pd.DataFrame, str]) -> Union[np.ndarray ,List[float]]:
    """
    Scoring routing for the model

    Parameters
    ----------
    raw_data : Union[pd.DataFrame, str]
        Raw text to score. It can be provided either using a Pandas dataframe with a column `text`
        or a `JSON` string with an attribute `text. Multiple texts can be submitted at the same
        time and they will be scored independently and separately.

    Returns
    -------
    Union[np.ndarray ,List[float]]
        A list with the probabilities of each of the texts provided to contain hate speech.
    """
    logging.info("Request received")

    try:
        if not isinstance(raw_data, pd.DataFrame):
            logging.info("[INFO] Parsing data for a JSON string")

            data = json.loads(raw_data)["data"]["text"]
        else:
            data = raw_data

        return MODEL.predict(data).tolist()

    except RuntimeError as E:
        logging.error(f'[ERR] Exception happened: {str(E)}')
        return f'Input {raw_data}. Exception was: {str(E)}'
