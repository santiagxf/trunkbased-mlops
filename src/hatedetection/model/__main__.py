"""
This module runs the training job for the hate detection model
"""
from common.jobs.runner import TaskRunner
from hatedetection.model.evaluation import resolve_and_evaluate

if __name__ == "__main__":
    tr = TaskRunner()
    tr.run_and_log(resolve_and_evaluate)
