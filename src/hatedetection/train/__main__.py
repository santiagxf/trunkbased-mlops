"""
This module runs the training job for the hate detection model
"""
from jobtools.runner import TaskRunner
from hatedetection.train.trainer import train_and_evaluate

if __name__ == "__main__":
    tr = TaskRunner()
    tr.run(train_and_evaluate)
