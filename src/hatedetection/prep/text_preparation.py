"""
This modules provides consistent preprocessing for all the text used in models at training
and inference type.
"""
import os
import glob
from typing import List, Tuple

import pandas as pd

def split_to_sequences(text: str, unique_words: int = 150, seq_len: int = 200) -> List[str]:
    """
    Splits a text sequence of an arbitrary length to sub-sequences of no more than `seq_len`
    words. Each sub-sequence will have `unique_words` words from the original text and the
    remaining words to match `seq_len` will be brought from the previous sub-sequence. This
    way we are able to retain some of the context from the previous sequence while splitting text.

    Parameters
    ----------
    text : str
        First number to add.
    unique_words : int
        Number of unique words to use on each subsequence.
    seq_len : int
        Number of total words to output on each sequence.

    Returns
    -------
    List[str]
        A list of sub-sequences of text of no more than `sequence_len`.
    """
    assert unique_words<seq_len

    words = text.split()
    n_seq = len(words)//unique_words + 1

    seqs = [' '.join(words[seq*unique_words:seq*unique_words + seq_len]) for seq in range(n_seq)]
    return seqs

def load_examples(data_path: str) -> Tuple[pd.Series, pd.Series]:
    """
    Loads data examples from CSV files stored in the given folder. Wildcards are supported.

    Parameters
    ----------
    data_path: str
        The path where the data is located.

    Returns
    -------
    Tuple[pd.Series, pd.Series]
        The text samples along with the corresponding ground truth
    """
    if os.path.isdir(data_path):
        data_path = os.path.join(data_path, "*.csv")

    if not str(data_path).endswith('.csv'):
        raise TypeError('Only CSV files are supported by the loading data procedure.')

    if not glob.glob(data_path):
        raise FileNotFoundError(f"Path or directory {data_path} doesn't exists")

    df = pd.concat(map(pd.read_csv, glob.glob(data_path)))
    df.loc[:,'text'] = df['text'].apply(split_to_sequences).explode('text').reset_index(drop=True)
    return df['text'], df['hate']
