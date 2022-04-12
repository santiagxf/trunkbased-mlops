"""
This modules provides consistent preprocessing for all the text used in models at training
and inference type.
"""
import os
import glob
import math
from typing import List, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

def split_to_sequences(text: str, unique_words, seq_len) -> List[str]:
    """
    Splits a text sequence of an arbitrary length to sub-sequences of no more than `seq_len`
    words. Each sub-sequence will have `unique_words` words from the original text and the
    remaining words to match `seq_len` will be brought from the previous sub-sequence. This
    way we are able to retain some of the context from the previous sequence while splitting text.

    Parameters
    ----------
    text : str
        Text you want to split in multiple subsequences.
    unique_words : int
        Number of unique words to use on each subsequence.
    seq_len : int
        Number of total words to output on each sequence. Each sequence would then contain
        `seq_len - unique_words` from the previous subsequence (context) and then `unique_words`
        from the current subsequence being generated.

    Returns
    -------
    List[str]
        A list of sub-sequences of text of no more than `sequence_len`.
    """
    assert unique_words<seq_len

    words = text.split()
    n_seq = math.ceil(len(words)/unique_words)

    seqs = [' '.join(words[seq*unique_words:seq*unique_words + seq_len]) for seq in range(n_seq)]
    return seqs

def load_examples(data_path: str, eval_size: float = 0, split_seq: bool = False, unique_words: int = 150,
                  seq_len: int = 200) -> Tuple[pd.Series, pd.Series]:
    """
    Loads data examples from CSV files stored in the given folder. Wildcards are supported.

    Parameters
    ----------
    data_path: str
        The path where the data is located.
    eval_size: float
        The evaluation proportion to withhold. If > 0, then returned series include evaluation
        data like (train_X, train_y, test_X, test_y)
    split_seq: bool
        Indicates if long sequences should be splitted in subsequences. If the case
        the index of the resulting data frame will indicate when subsequences belonged
        to the same sequence.
    unique_words: int
        Number of unique words to use on each subsequence.
    seq_len : int
        Number of total words to output on each sequence. Each sequence would then contain
        `seq_len - unique_words` from the previous subsequence (context) and then `unique_words`
        from the current subsequence being generated.

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
    if eval:
        train, test = train_test_split(df, test_size=eval_size, stratify=df['hate'])
    else:
        train = df

    if split_seq:
        train.loc[:,'text'] = train['text'].apply(split_to_sequences,
                                            unique_words=unique_words,
                                            seq_len=seq_len).explode('text').reset_index(drop=True)
    
    if eval:
        if split_seq:
            test.loc[:,'text'] = test['text'].apply(split_to_sequences,
                                            unique_words=unique_words,
                                            seq_len=seq_len).explode('text').reset_index(drop=True)
            return train['text'], train['hate'], test['text'], test['hate']

    return train['text'], train['hate']
