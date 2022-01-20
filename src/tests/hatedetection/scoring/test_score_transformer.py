"""Unit tests for score_transformer
"""
import pandas as pd
import pytest
from azureml.core import Workspace
from azureml.core.authentication import AzureCliAuthentication
from hatedetection.score import score_transformer
from hatedetection.prep.text_preparation import split_to_sequences

@pytest.fixture(scope="module")
def text_samples():
    return pd.DataFrame(data=[
        {"text": "Mude seus pensamentos e você pode mudar seu mundo."},
        {"text": "Quando você não pode mudar a direção do vento, mude a direção de sua vela."}])

@pytest.mark.inference
def test_init_from_aml_workspace(ws_config_file):
    """ Unit test for score_transformer.init()
    """
    # Authenticate
    cli_auth = AzureCliAuthentication()

    # Get Azure ML Workspace information
    ws = Workspace.from_config(path=ws_config_file, auth=cli_auth)

    score_transformer.init(from_workspace=True, workspace=ws)
    assert score_transformer.MODEL is not None

@pytest.mark.inference
def test_run_scores(ws_config_file, text_samples):
    """Unit test for score_transformer.run()
    """
    # Authenticate
    cli_auth = AzureCliAuthentication()
    ws = Workspace.from_config(path=ws_config_file, auth=cli_auth)

    score_transformer.init(from_workspace=True, workspace=ws)
    scores = score_transformer.run(raw_data=text_samples)

    # Test scores is within range (0,1)
    assert all(score >= 0 for score in scores)
    assert all(score <= 1 for score in scores)
    # Test number of scores returned is the same as the number of rows of input data
    assert len(scores) == len(text_samples)
