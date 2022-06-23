"""
Training routine for a language model using transformers
"""
import logging
from typing import Dict, Any
from types import SimpleNamespace

import mlflow
from mlflow.models.signature import ModelSignature
from mlflow.types.schema import Schema, ColSpec
from mlflow.types import DataType

from transformers import Trainer, TrainingArguments
from hatedetection.model.hate_detection_classifier import HateDetectionClassifier
from hatedetection.model.evaluator import compute_classification_metrics
from hatedetection.train.datasets import ClassificationDataset
from hatedetection.prep.text_preparation import load_examples

def train_and_evaluate(input_dataset: str, eval_dataset: str,
                       params: SimpleNamespace) -> Dict[str, Dict[str, Any]]:
    """
    Trains and evaluete the hate detection model

    Parameters
    ----------
    input_dataset: Union[str, PathLike]
        The path to the training dataset
    eval_dataset: Union[str, PathLike]
        The path to the evaluation dataset
    task: SimpleNamespace
        The training configuration for this task

    Returns
    -------
    Dict[str, Dict[str, Any]]
        A dictonary containing the keys `arguments`, `metrics` and `artifacts` as the
        results of the run.
    """
    classifier = HateDetectionClassifier()
    classifier.build(baseline=params.model.baseline)
    classifier.split_unique_words = params.data.preprocessing.split_unique_words
    classifier.split_seq_len = params.data.preprocessing.split_seq_len

    if eval_dataset:
        X_train, y_train = load_examples(input_dataset,
                                                     split_seq=True,
                                                     unique_words=classifier.split_unique_words,
                                                     seq_len = classifier.split_seq_len)
        X_eval, y_eval = load_examples(eval_dataset,
                                                   split_seq=True,
                                                   unique_words=classifier.split_unique_words,
                                                   seq_len = classifier.split_seq_len)
    else:
        logging.warning('[WARN] Evaluation will happen over the training dataset as evaluation \
                        dataset has not been provided.')
        X_train, y_train, X_eval, y_eval = load_examples(input_dataset,
                                                    eval_size=0.3,
                                                    split_seq=True,
                                                    unique_words=classifier.split_unique_words,
                                                    seq_len = classifier.split_seq_len)

    train_dataset = ClassificationDataset(examples=X_train,
                                          labels=y_train,
                                          tokenizer=classifier.tokenizer)
    eval_dataset = ClassificationDataset(examples=X_eval,
                                         labels=y_eval,
                                         tokenizer=classifier.tokenizer)

    training_args = TrainingArguments(**vars(params.trainer))

    trainer = Trainer(
        model=classifier.model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_classification_metrics,
    )

    logging.info('[INFO] Training will start now')
    history = trainer.train()

    logging.info('[INFO] Evaluation will start now')
    evaluation_metrics = trainer.evaluate()

    logging.info('[INFO] Training completed. Persisting model and tokenizer.')
    artifacts = classifier.save_pretrained(f"{params.model.output_dir}/{params.model.name}")

    signature = ModelSignature(
        inputs=Schema([
            ColSpec(DataType.string, "text"),
        ]),
        outputs=Schema([
            ColSpec(DataType.integer, "hate"),
            ColSpec(DataType.double, "confidence"),
        ]))

    mlflow.log_metrics(dict(filter(lambda item: item[1] is not None, evaluation_metrics.items())))
    mlflow.log_params(history.metrics)
    mlflow.pyfunc.log_model(artifact_path=params.model.name,
                            code_path=['hatedetection'],
                            python_model=classifier,
                            artifacts=artifacts,
                            signature=signature)

    return {
        'metrics': evaluation_metrics,
        'arguments': history.metrics,
        'artifacts': artifacts.keys()
    }
