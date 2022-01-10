

import logging
import shutil
from typing import Union
from os import PathLike

import pandas as pd
import torch
from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.models.auto import AutoModelForSequenceClassification

try:
    from hatedetection.prep.text_preparation import split_to_sequences
except ImportError:
    from ..prep.text_preparation import split_to_sequences
    logging.warning("[WARN] hatedetection package failed to import. Used relative importing instead.")


class HateDetectionClassifier:
    def __init__(self):
        self.model_name = 'hate-pt-speech'
        
    def load(self, path: str):
        if path.endswith(".zip"):
            logging.info(f"[INFO] Unpacking archive {path}")

            self.model_path = f'./{self.model_name}'
            shutil.unpack_archive(path, self.model_path)
        else:
            self.model_path = path

        logging.info("[INFO] Loading transformer tokenizer")
        self.build(self.model_path)

        logging.info("[INFO] Switching to evaluation mode")
        _ = self.model.eval()

    def build(self, baseline: str):
        """
        Creates a `transformers` tokenizer and model using the given baseline URL. `baseline is
        the url of a `huggingface` model or the url of a folder containing a `transformer` model.

        Parameters
        ----------
        baseline: str
            The baseline model. This can be a huggingface URL or a local path.
        """
        self.tokenizer = AutoTokenizer.from_pretrained(baseline)
        self.model = AutoModelForSequenceClassification.from_pretrained(baseline)
    
    def save_pretrained(self, save_directory: Union[str, PathLike]):
        """
        Saves the model to a directory. Multiple files are generated.
        """
        self.tokenizer.save_pretrained(save_directory)
        self.model.save_pretrained(save_directory)
    
    def predict(self, data: Union[list, pd.Series, pd.DataFrame]):
        if isinstance(data, pd.DataFrame):
            data = data["text"]
        elif isinstance(data, list):
            data = pd.Series(data)
        data = data.apply(split_to_sequences).explode()
        
        inputs = self.tokenizer(list(data), padding=True, truncation=True, return_tensors='pt')
        predictions = self.model(**inputs)
        probs = torch.nn.Softmax(dim=1)(predictions.logits)

        logging.info("[INFO] Computing classes")
        hate = probs.argmax(axis=1)

        data = data.reset_index()
        data['hate'] = hate.detach().numpy()
        scores = data[['index', 'hate']].groupby('index').agg(pd.Series.mode)['hate']

        return scores
    
    def predict_proba(self, data: Union[list, pd.Series, pd.DataFrame]):
        if isinstance(data, pd.DataFrame):
            data = data["text"]
        elif isinstance(data, list):
            data = pd.Series(data)
        data = data.apply(split_to_sequences).explode()
        
        inputs = self.tokenizer(list(data), padding=True, truncation=True, return_tensors='pt')
        predictions = self.model(**inputs)
        probs = torch.nn.Softmax(dim=1)(predictions.logits)

        logging.info("[INFO] Building results with hate probabilities only (class=1)")
        hate = probs.T[1]

        data = data.reset_index()
        data['hate'] = hate.detach().numpy()
        scores = data[['index', 'hate']].groupby('index').agg('mean')['hate']

        return scores