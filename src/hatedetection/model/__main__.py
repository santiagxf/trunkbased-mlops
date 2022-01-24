"""
This module runs the evaluation job for the hate detection model
"""
import time
from common.jobs.runner import ExperimentRunner
from hatedetection.model.evaluation import resolve_and_compare

if __name__ == "__main__":
    tr = ExperimentRunner()
    tr.run_and_log(resolve_and_compare)
    time.sleep(5)
