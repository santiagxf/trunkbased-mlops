"""
This module provides orchestration to run and execute a job in Azure ML
"""
import os
import logging
from time import sleep
from typing import Callable, Dict, Any
from enum import Enum
from common.jobs.arguments import TaskArguments, get_args_from_signature

try:
    from azureml.core import Run
    from azureml.core.run import RunEnvironmentException
except ImportError:
    logging.info("[INFO] Method to_azureml won't be available as azureml-sdk is not installed")


__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

class StringEnum(Enum):
    """
    Provides a way to work with enum string values in Python.
    """
    def __str__(self):
        return str(self.value)

class TaskResultKey(StringEnum):
    """
    Represents all the type of objects the TaskRunner can take as a result.
    """
    METRICS = 'metrics'
    ARTIFACTS = 'artifacts'
    ARGUMENTS = 'arguments'

class TaskRunner():
    """
    Allows an easy way to run a task in Azure ML and log any input into the run. Tasks are specified
    as a callable with arguments that are automatically parsed from the signature. The method should
    return a dictionary with keys "metrics", "arguments" and "artifacts".
    """
    def __init__(self, args: TaskArguments = None) -> None:
        """
        Initializes the TaskRunner. If `args` is indicated, then the argument's won't be parsed from the
        command line. Otherwise they will.
        """
        self.run = None
        self.task_arguments = args
        try:
            if Run is not None:
                self.run = Run.get_context()
            else:
                logging.warning("[WARN] azureml-sdk is not installed. Logging won't happen in workspace")
        except RunEnvironmentException:
            logging.warning("[WARN] Unable to get current run in Azure ML. Logging won't happen in workspace.")

    def log_on_run(self, key: str, value: Any) -> None:
        """
        Logs a given value in the current run with a key. This method can log
        any type of data.

        Parameters
        ----------
        key: str
            The name of the metric to log
        value: Any
            The value to log. This method supports logging list of elements too.
        """
        if self.run:
            if isinstance(value, list):
                if len(value) > 0:
                    try:
                        self.run.log_list(key, value)
                    except RuntimeError:
                        logging.error(f"[ERROR] Unable to log key {key} of type [LIST] {type(value)}.")
                else:
                    logging.warning(f"[WARN] Attempt to log an list object with no items. Key was {key}.")
            else:
                try:
                    self.run.log(key, value)
                except RuntimeError:
                    logging.error(f"[ERROR] Unable to log with key {key} of type {type(value)}.")
        else:
            logging.warning(f"[WARN] Logging key '{key}' ignored as no run available.")

    def to_azureml(self, results: Dict[TaskResultKey, Dict[str, Any]]) -> None:
        """
        Takes a dictionary containing all the results from a run execution and logs in the
        current run. Metrics and arguments are logged as "run metrics" and artifacts are
        uploaded to the run as files.

        Parameters
        ----------
        results: Dict[TaskResultKey, Dict[str, Any]]
            A dictonary containing the keys `arguments`, `metrics` and `artifacts` to log into
            the run.
        """

        task_results = { TaskResultKey(key): values for key, values in results.items() }

        if TaskResultKey.ARGUMENTS in task_results.keys():
            for arg, value in task_results[TaskResultKey.ARGUMENTS].items():
                logging.info(f"[INFO] Logging argument {arg} with value {str(value)}")
                self.log_on_run(arg, value)

        if TaskResultKey.METRICS in task_results.keys():
            for metric, value in task_results[TaskResultKey.METRICS].items():
                logging.info(f"[INFO] Logging metric {metric} with value {str(value)}")
                self.log_on_run(metric, value)

        if TaskResultKey.ARTIFACTS in task_results.keys():
            for artifact_path in task_results[TaskResultKey.ARTIFACTS]:
                base_name=os.path.splitext(os.path.basename(artifact_path))[0]

                logging.info(f"[INFO] Uploading artifact {base_name} at {artifact_path}")
                self.run.upload_file(name=base_name, path_or_stream=artifact_path)

    def run_and_log(self, task: Callable[[], Dict[TaskResultKey, Dict[str, Any]]]) -> None:
        """
        Runs the given task specified as a method and log any of the returning elements from the run
        in Azure Machine Learning if possible. The method should return a dictionary containing the
        elements in `TaskResultKey` and they will be properly logged in the run as metrics or assets.

        Parameters
        ----------
        task: Callable[[], Dict[TaskResultKey, Dict[str, Any]]]
            The task you want to run. This method can be any that returns a dictionary with keys
            `arguments`, `metrics` and `artifacts`. Parameters for this method will either be
            demanded from the command line or have to be indicated in the constructor of the
            `TaskRunner` object.
        """
        if self.task_arguments is None:
            args = vars(get_args_from_signature(task))
        else:
            args = self.task_arguments.resolve_for_method(task)

        outputs = task(**args)
        self.to_azureml(outputs)
        sleep(5) # This line looks is a hack for some extrage behaviour in AML. Metrics are not logged otherwise
