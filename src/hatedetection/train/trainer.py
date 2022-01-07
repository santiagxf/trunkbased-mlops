"""
Training routine for a language model using transformers
"""
import shutil
import logging
from typing import Dict, Any
from types import SimpleNamespace

from transformers import Trainer, TrainingArguments
from hatedetection.model.hate_detection_classifier import HateDetectionClassifier
from hatedetection.model.evaluation import compute_classification_metrics
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

    examples_train, labels_train = load_examples(input_dataset)
    if eval_dataset:
        examples_eval, labels_eval = load_examples(eval_dataset)
    else:
        logging.warning('[WARN] Evaluation will happen over the training dataset as evaluation \
                        dataset has not been provided.')
        examples_eval, labels_eval = examples_train, labels_train

    train_dataset = ClassificationDataset(examples=examples_train,
                                          labels=labels_train,
                                          tokenizer=classifier.tokenizer)
    eval_dataset = ClassificationDataset(examples=examples_eval,
                                         labels=labels_eval,
                                         tokenizer=classifier.tokenizer)

    training_args = TrainingArguments(**vars(params.trainer))

    trainer = Trainer(
        model=classifier.model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_classification_metrics
    )

    logging.info('[INFO] Training will start now')
    history = trainer.train()

    logging.info('[INFO] Evaluation will start now')
    evaluation_metrics = trainer.evaluate()

    logging.info('[INFO] Training completed. Persisting model and tokenizer.')
    saved_location=f"{params.model.output_dir}/{params.model.name}"
    classifier.save_pretrained(saved_location)

    logging.info('[INFO] Zipping assets to target directory')
    shutil.make_archive(saved_location, format='zip', root_dir=saved_location, base_dir='./')

    return {
        'metrics': evaluation_metrics,
        'arguments': history.metrics,
        'artifacts': [ f'{saved_location}.zip' ]
    }
