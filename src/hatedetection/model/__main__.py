"""
This module runs the evaluation job for the hate detection model
"""
import time
from jobtools.runner import TaskRunner
from hatedetection.model.evaluation import resolve_and_compare

if __name__ == "__main__":
    tr = TaskRunner()
    tr.run(resolve_and_compare)
    time.sleep(3)
