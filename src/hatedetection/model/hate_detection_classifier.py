

import logging
import shutil
import math
import os
import pathlib
import numpy as np
from typing import Dict, Union
from os import PathLike
from mlflow.pyfunc import PythonModel, PythonModelContext

import pandas as pd
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

    def get_artifacts(self) -> Dict[str, str]:
        """
        Gets a dictionary with the paths to all the artifacts persisted for
        this model. Accordingly, this method can only be called after the model
        has been persisted.

        Returns
        -------
        Dict[str, str]
            A dictionary containing all the paths to the artifacts of the model. Keys
            contains the name of the artifacts (file name with no extension), and the
            values contians the path to the artifact.

        Raises
        ------
        ValueError
            If the model has never been saved to disk.
        """
        if self.artifacts_path is None:
            raise ValueError("Can't get the artificats of an unpersisted model. Call save_pretrained first.")

        artifacts = {}
        for rootdir, _, files in os.walk(self.artifacts_path):
            for file in files:
                if not os.path.basename(file).startswith('.'):
                    artifacts[pathlib.Path(file).stem]=os.path.join(rootdir, file)
        return artifacts
        
    def load(self, path: PathLike):
        """Loads the model from a folder where artifacts are stored, including the model and its
        corresponding tokenizer.

        Parameters
        ----------
        path : PathLike
            The path where the artifacts are stored. The path can be a folder or it can be
            zipped in a zip file, in which case they will be unzipped first.
        """
        if str(path).endswith(".zip"):
            logging.info(f"[INFO] Unpacking archive {path}")

            self.artifacts_path = f'./{self.model_name}/'
            shutil.unpack_archive(path, self.artifacts_path)
        else:
            self.artifacts_path = path

        logging.info("[INFO] Loading transformer")
        self.build(self.artifacts_path)

        logging.info("[INFO] Switching to evaluation mode")
        _ = self.model.eval()

    def load_context(self, context: PythonModelContext):
        """Loads the model from an MLFlow context

        Parameters
        ----------
        context : PythonModelContext
            Model context
        """
        artifacts_path = os.path.dirname(context.artifacts["pytorch_model"])
        self.load(artifacts_path)

    def build(self, baseline: str, tokenizer: str = None):
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
    
    def save_pretrained(self, save_directory: Union[str, PathLike] = None) -> str:
        """
        Saves the model to a directory. Multiple files are generated.
        """
        self.artifacts_path = save_directory or self.artifacts_path or self.model_name
        self.tokenizer.save_pretrained(self.artifacts_path)
        self.model.save_pretrained(self.artifacts_path)

        return save_directory
    
    def predict(self, context: PythonModelContext, model_input: Union[list, pd.Series, pd.DataFrame]):
        if isinstance(model_input, pd.Series):
            data = model_input
        elif isinstance(model_input, pd.DataFrame):
            data = model_input["text"]
        elif isinstance(model_input, list):
            data = pd.Series(model_input)
        elif isinstance(model_input, np.ndarray):
            data = pd.Series(model_input)
        else:
            raise TypeError(f"Unsupported type {type(model_input).__name__}")
        
        data = data.apply(split_to_sequences,
                          unique_words=self.split_unique_words,
                          seq_len=self.split_seq_len).explode()
        
        inputs = self.tokenizer(list(data), padding=True, truncation=True, return_tensors='pt')
        predictions = self.model(**inputs)
        probs = torch.nn.Softmax(dim=1)(predictions.logits)

        logging.info("[INFO] Computing classes")
        hate = probs.argmax(axis=1)

        data = data.reset_index()
        data['hate'] = hate.detach().numpy()
        scores = data[['index', 'hate']].groupby('index').agg(pd.Series.mode)['hate']

        return scores
    
    def predict_proba(self, model_input: Union[list, pd.Series, pd.DataFrame]):
        if isinstance(model_input, pd.Series):
            data = model_input
        elif isinstance(model_input, pd.DataFrame):
            data = model_input["text"]
        elif isinstance(model_input, list):
            data = pd.Series(model_input)
        elif isinstance(model_input, np.ndarray):
            data = pd.Series(model_input)
        else:
            raise TypeError(f"Unsupported type {type(model_input).__name__}")

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

    def predict_batch(self, model_input: Union[list, pd.Series, pd.DataFrame], batch_size: int = 64):
        """
        Calls the predict API using batches of data instead of running it all at once.

        Parameters
        ----------
        model_input : Union[list, pd.Series, pd.DataFrame]
            Inputs of the model.
        batch_size : int, optional
            Size of the batches, by default 64

        Returns
        -------
        np.ndarray
            The model predictions for the input data.
        """
        sample_size = len(model_input)
        batches_idx = range(0, math.ceil(sample_size / batch_size))
        scores = np.zeros(sample_size)

        for batch_idx in batches_idx:
            batch_from = batch_idx * batch_size
            batch_to = batch_from + batch_size
            scores[batch_from:batch_to] = self.predict(model_input.iloc[batch_from:batch_to])
        
        return scores
