from typing import Dict
import pandas as pd
from sklearn.metrics import f1_score, precision_score, confusion_matrix
from sklearn.metrics import accuracy_score, recall_score, precision_recall_fscore_support
from common.models.model_management import download_model_from_context
from hatedetection.prep.text_preparation import load_examples 
from hatedetection.model.hate_detection_classifier import HateDetectionClassifier

def compute_classification_metrics(pred: Dict) -> Dict[str, float]:
    """
    Computes the metrics given predictions of a torch model

    Parameters
    ----------
    pred: Dict
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

def resolve_and_evaluate(model_name: str, eval_dataset: str, threshold: float = 0.5) -> Dict[str, float]:
    """
    Resolves the model from it's name and runs the evaluation routine.

    Parameters
    ----------
    model_name: str
        Name of the model to get. The model will be downloaded from the model registry.
    eval_dataset: str
        Path that leads to the dataset.
    threshold: float
        The workspace to load the model from.
        If not indicated, it will use the default model.

    Returns
    -------
    Dict[str, float]
       A dictionary containing the keys `f1_score`, `precision`, `recall`, `specificity` and `accuracy` as the results of the run.
    """
    model_path = download_model_from_context(model_name)
    return evaluate(model_path, eval_dataset, threshold)

def evaluate(model_path: str, eval_dataset: str, threshold: float = 0.5) -> Dict[str, float]:
    """
    Evaluation routine for the model
    
    Parameters
    ----------
    model_path: str
        Path to where the model is stored.
    eval_dataset: str
        Path that leads to the dataset.
    threshold: float
        The workspace to load the model from.
        If not indicated, it will use the default model.

    Returns
    -------
    Dict[str, float]
       A dictionary containing the keys `f1_score`, `precision`, `recall`, `specificity` and `accuracy` as the results of the run.
    """
    # Get the path for the dataset from the input
    text, labels = load_examples(eval_dataset)
    model = HateDetectionClassifier()
    model.load(model_path)

    # Create a new pandas dataframe from the pandas.Series created in load_examples
    df = pd.concat([text], axis=1)

    # Runs the model and transform the results into binaries according to the threshold
    scores     = model.predict_proba(data=df)
    bin_scores = [1 if score > threshold else 0 for score in scores]

    tn, fp, fn, tp = confusion_matrix(labels, bin_scores).ravel()

    # Metrics
    f1 = f1_score(labels, bin_scores)
    precision = precision_score(labels, bin_scores)
    recall = recall_score(labels, bin_scores)
    specificity = tn / (tn+fp) if (tn+fp) != 0 else 0
    accuracy = accuracy_score(labels, bin_scores)

    # Output a dict with the calculated metrics
    metrics = {
        "f1_score": f1,
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "accuracy": accuracy
    }

    return {'metrics': metrics}
