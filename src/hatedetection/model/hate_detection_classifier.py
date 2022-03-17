import logging
import math
import os
import pathlib

from os import PathLike
from typing import Dict, Union
from mlflow.pyfunc import PythonModel, PythonModelContext

import pandas as pd
import numpy as np
import torch

from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.models.auto import AutoModelForSequenceClassification

try:
    from hatedetection.prep.text_preparation import split_to_sequences
except ImportError:
    from ..prep.text_preparation import split_to_sequences
    logging.warning("[WARN] hatedetection package failed to import. Used relative importing instead.")


class HateDetectionClassifier(PythonModel):
    def __init__(self, model_name = 'hate-pt-speech'):
        self.model_name = model_name
        self.artifacts_path = None
        self.split_unique_words = 150
        self.split_seq_len = 200
        self.batch_size = 64
        
    def load_context(self, context: PythonModelContext):
        """Loads the model from an MLFlow context

        Parameters
        ----------
        context : PythonModelContext
            Model context
        """
        artifacts_path = os.path.dirname(context.artifacts["pytorch_model"])
        logging.info("[INFO] Loading transformer")
        
        self.build(artifacts_path, eval=True)

    def build(self, baseline: str, tokenizer: str = None, eval: bool = False):
        """
        Creates a `transformers` tokenizer and model using the given baseline URL. `baseline is
        the url of a `huggingface` model or the url of a folder containing a `transformer` model.

        Parameters
        ----------
        baseline: str
            The baseline model. This can be a huggingface URL or a local path.
        tokenizer: str
            The baseline tokenizer. This can be a huggingface URL or a local path. If None, then
            the same baseline model will be used.
        """
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer or baseline)
        self.model = AutoModelForSequenceClassification.from_pretrained(baseline)
        
        if eval:
            logging.info("[INFO] Switching to evaluation mode")
            _ = self.model.eval()
    
    def save_pretrained(self, save_directory: Union[str, PathLike] = None) -> Dict[str, str]:
        """
        Saves the model to a directory. All the required artifacts are persisted.

        Returns
        -------
        Dict[str, str]
            A dictionary containing all the paths to the artifacts of the model. Keys
            contains the name of the artifacts (file name with no extension), and the
            values contians the path to the artifact.
        """

        self.artifacts_path = save_directory or self.artifacts_path or self.model_name
        self.tokenizer.save_pretrained(self.artifacts_path)
        self.model.save_pretrained(self.artifacts_path)

        artifacts = {}
        for rootdir, _, files in os.walk(self.artifacts_path):
            for file in files:
                if not os.path.basename(file).startswith('.'):
                    artifacts[pathlib.Path(file).stem]=os.path.join(rootdir, file)
        return artifacts

    def predict_batch(self, data: Union[list, pd.Series, pd.DataFrame]):
        """
        Predicts a single batch of data.

        Parameters
        ----------
        data: Union[list, pd.Series, pd.DataFrame]
            The data you want to run the model on.

        Return
        ------
        pd.DataFrame
            A dataframe with a column hate with the probabilities of the given text of containing hate.
        """
        if isinstance(data, pd.DataFrame):
            data = data['text']
    
        data = data.apply(split_to_sequences,
                          unique_words=self.split_unique_words,
                          seq_len=self.split_seq_len).explode()
        
        inputs = self.tokenizer(list(data), padding=True, truncation=True, return_tensors='pt')
        predictions = self.model(**inputs)
        probs = torch.nn.Softmax(dim=1)(predictions.logits)
        
        logging.info("[INFO] Building results with hate probabilities only (class=1)")
        hate = probs.T[1]

        data = data.reset_index()
        data['hate'] = hate.detach().numpy()
        scores = data[['index', 'hate']].groupby('index').agg('mean')['hate']

        return scores

    def predict(self, context: PythonModelContext, model_input: Union[list, pd.Series, pd.DataFrame]):
        sample_size = len(model_input)
        batches_idx = range(0, math.ceil(sample_size / self.batch_size))
        scores = np.zeros(sample_size)

        for batch_idx in batches_idx:
            batch_from = batch_idx * self.batch_size
            batch_to = batch_from + self.batch_size
            scores[batch_from:batch_to] = self.predict_batch(model_input.iloc[batch_from:batch_to])
        
        return scores
