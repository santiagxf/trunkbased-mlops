import pytest
import pandas as pd
from hatedetection.prep.text_preparation import split_to_sequences


raw_data = pd.DataFrame(data=[
    {"text": "Mude seus pensamentos e você pode mudar seu mundo."},
    {"text": "Mude seus pensamentos e você pode mudar seu mundo. \
        Quando você não pode mudar a direção do vento, mude a direção de sua vela."}])
data_samples = [raw_data]

@pytest.mark.parametrize("data", data_samples)
def test_split_to_sequence_len(data: pd.DataFrame):
    """ Unit test for score_transformer.split_to_sequences()
    """
    unique_words = 5
    seq_len = 10    
    
    data_split = data.apply(split_to_sequences,
                            unique_words=unique_words,
                            seq_len=seq_len).explode()

    assert all(data_split['text'].str.len() <= seq_len)