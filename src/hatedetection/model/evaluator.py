import logging
import torch
import mlflow
import numpy as np
import math

from typing import Dict, Any
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from statsmodels.stats.contingency_tables import mcnemar
from hatedetection.prep.text_preparation import load_examples 

def compute_classification_metrics(pred: Dict[str, torch.Tensor]) -> Dict[str, float]:
    """
    Computes the classification metrics for the given predictions returned by a 
    Torch model.

    Parameters
    ----------
    pred: Dict[str, torch.Tensor]
        Predictions returned from the model.

    Returns
    -------
    Dict[str, float]:
        The metrics computed, inclusing `accuracy`, `f1`, `precision`, `recall` and `support`.
    """
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    precision, recall, f1, support = precision_recall_fscore_support(labels, preds, average='weighted')
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall,
        'support': support
    }

def resolve_and_compare(model_name: str, champion: str, challenger: str, eval_dataset: str,
                        class_output: str, confidence: float = 0.05) -> Dict[str, float]:
    """
    Resolves the model from it's name and runs the evaluation routine.

    Parameters
    ----------
    model_name: str
        Name of the model to get. The model will be downloaded from the model registry.
    champion: str
        Champion version of the model. This can be a number, or a label like `latest` or `Production`
    challenger: str
        Challenger version of the model. This can be a number, or a label like `latest` or `Production`
    eval_dataset: str
        Path that leads to the dataset.
    class_output: str
        Name of the output produced by the model where the predicted class is placed.
    confidence: float
        The condifidence level of the test (p-value). Defaults to 95% (0.05)

    Returns
    -------
    Dict[str, float]
       A dictionary containing the keys `statistic`, `pvalue` as a result of the statistical test.
    """
    
    logging.info(f"[INFO] Comparing models {champion} vs {challenger}")
    return compute_mcnemmar(_model_uri_or_none(model_name, champion),
                            _model_uri_or_none(model_name, challenger),
                            eval_dataset,
                            class_output,
                            confidence)

def _model_uri_or_none(model_name: str, version: str) -> str:
    """
    Build a model URI in MLFlow format for a given model in the registry. If
    there is no model registered, then it returns None.

    Parameters
    ----------
    model_name : str
        Name of the model
    version : str
        This can be a number, or a label like `latest` or `Production`

    Returns
    -------
    str
        The model URI or None.
    """
    client = mlflow.tracking.MlflowClient()
    if not version.isdigit():
        if version == 'latest':
            if (len(client.get_latest_versions(model_name)) == 0):
                return None

        if len(client.get_latest_versions(model_name, stages=[version])) == 0:
            return None

    return f"models:/{model_name}/{version}"


def _predict_batch(model, data, class_field, batch_size = 64):
    sample_size = len(data)
    batches_idx = range(0, math.ceil(sample_size / batch_size))
    scores = np.zeros(sample_size)

    for batch_idx in batches_idx:
        bfrom = batch_idx * batch_size
        bto = bfrom + batch_size
        scores[bfrom:bto] = model.predict(data.iloc[bfrom:bto])[class_field]
    
    return scores

def compute_mcnemmar(champion_path: str, challenger_path: str, eval_dataset: str,
                     class_output: str, confidence: float = 0.05) -> Dict[str, Any]:
    """
    Compares two hate detection models and decides if the two models make the same mistakes or not.
    Note that this method doesn't tell which one is better but if the models are statistically
    different. It uses the McNemmar test.

    Parameters
    ----------
    champion_path: str
        Path to the champion model.
    challenger_path: str
        Path to the challenger model.
    eval_dataset: str
        Path to the evaluation dataset.
    class_output: str
        Name of the output produced by the model where the predicted class is placed.
    confidence: float
        The condifidence level of the test (p-value). Defaults to 95% (0.05)

    Returns
    -------
    Dict[str, Dict[str, float]]:
        A dictionary containing the keys `statistic`, `pvalue` as a result of the statistical test.
    """
    mlflow.log_param("test", "mcnemar")
    mlflow.log_param("confidence", confidence)

    if champion_path and challenger_path:
        text, _ = load_examples(eval_dataset)
        champion_model = mlflow.pyfunc.load_model(champion_path)
        champion_scores = _predict_batch(champion_model, text, class_output)

        logging.info("[INFO] Unloading champion object from memory")
        del champion_model
        torch.cuda.synchronize()

        challenger_model = mlflow.pyfunc.load_model(challenger_path)
        challenger_scores = _predict_batch(challenger_model, text, class_output)

        logging.info("[INFO] Unloading challenger object from memory")
        del challenger_model
        torch.cuda.synchronize()

        cont_table = confusion_matrix(champion_scores, challenger_scores)
        results = mcnemar(cont_table, exact=False)

        metrics = {
            "statistic": results.statistic,
            "pvalue": results.pvalue,
        }

    else:
        metrics = {
            "statistic": 0,
            "pvalue": 0,
        }
        mlflow.log_param("warning", "No champion model indicated")

    mlflow.log_metrics(metrics)
    return metrics
