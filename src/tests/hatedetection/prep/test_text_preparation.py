"""Unit tests for text_preparation
"""
from cProfile import label
import pandas as pd
import pytest
from azureml.core import Workspace
from azureml.core.authentication import AzureCliAuthentication
from hatedetection.score import score_transformer
from hatedetection.prep.text_preparation import split_to_sequences, load_examples

text = "Mude seus pensamentos e você pode mudar seu mundo. \
        Quando você não pode mudar a direção do vento, mude a direção de sua vela."

@pytest.mark.parametrize("text, unique_words, seq_len", (text, 5, 10))
def test_split_to_sequence_len(text, unique_words, seq_len):
    """ Unit test for hatedetection.prep.text_preparation.split_to_sequences()
    """
    sequences = split_to_sequences(
        text=text,
        unique_words=unique_words,
        seq_len=seq_len)
    n_words = [len(seq.split()) for seq in sequences]
    assert all(n <= seq_len for n in n_words)


@pytest.mark.parametrize("data_path", "../datasets/portuguese-hate-speech-tweets-eval/data/*.csv")
def test_load_examples(data_path):
    text, labels = load_examples(data_path)

    assert len(text) == len(labels)

    assert text.dtype == 'object'
    assert labels.dtype == 'float'

    assert labels.all(label in [0,1] for label)
