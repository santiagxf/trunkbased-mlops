"""
This module runs the training job for the hate detection model
"""
from common.jobs.runner import ExperimentRunner
from hatedetection.train.trainer import train_and_evaluate

if __name__ == "__main__":
    tr = ExperimentRunner()
    tr.run_and_log(train_and_evaluate)
