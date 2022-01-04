"""
Provides a convenient way to read and parse arguments for Python scripts being run using
the command line.
"""

import pathlib
import logging
import argparse
import inspect
from types import SimpleNamespace
from typing import Callable, Dict, Any

import json
import yaml

def yml2config(config_file_path: str) -> SimpleNamespace:
    """
    Loads a `YAML` file containing representing configuration and parses
    it as a `SimpleNamespace` object.

    Parameters
    ----------
    config_file_path : str
        Path where the `YAML` file is located.

    Returns
    -------
    SimpleNamespace
        The given configuration parsed as a namespace.
    """
    try:
        config_path = pathlib.Path(config_file_path)
        if config_path.is_dir():
            logging.warning(f"[WARN] Configuration path '{config_file_path}' is a directory, \
                            but a yml file is expected. Looking for the first file")
            config_file_path = next(config_path.glob('*.yml'))

        with open(config_file_path, encoding='utf-8') as file:
            config = yaml.load(file, Loader=yaml.FullLoader)

            # This conversion allows to parse nested dictionaries into a SimpleNamespace.
            namespace = json.loads(json.dumps(config),
                                object_hook=lambda item: SimpleNamespace(**item))

        return namespace

    except ValueError as err:
        msg = f"When loading the configuration file from '{config_file_path}', \
                the following error happened: {err}"
        raise argparse.ArgumentTypeError(msg)

def get_args_from_signature(method: Callable) -> argparse.Namespace:
    """
    Automatically parses all the arguments to match an specific method. The method should
    implement type hinting in order for this to work. All arguments required by the method
    will be also required by the parser. To match bash conventions, arguments with underscore
    will be parsed as arguments with upperscore. For instance `from_path` will be requested
    as `--from-path`. Signature arguments with type `SimpleNamespace` have to be specified
    using a `YAML` file.

    Parameters
    ----------
    method: Callable
        The method the arguments should be extracted from.

    Returns
    -------
    argparse.Namespace
        The arguments parsed. You can call `method` with `**vars(...)` then.
    """
    parser = argparse.ArgumentParser()
    fullargs = inspect.getfullargspec(method)
    args_annotations = dict(filter(lambda key: key[0] != 'return', fullargs.annotations.items()))

    required_args_idxs = len(args_annotations) - len(fullargs.defaults if fullargs.defaults else [])
    for idx, (arg, arg_type) in enumerate(args_annotations.items()):
        is_required = idx < required_args_idxs

        if arg_type is SimpleNamespace:
            if not is_required:
                raise ValueError("An argument of type SimpleNamespace can't be optional. Remove default values.")
            parser.add_argument(f"--{arg.replace('_','-')}", dest=arg, type=yml2config, required=is_required)
        else:
            parser.add_argument(f"--{arg.replace('_','-')}", dest=arg, type=arg_type, required=is_required)

    return parser.parse_args()

class TaskArguments():
    """
    Provides a way to run the `TaskRunner` without executing Python code from
    Python command line. So running `python myfile.py --arg1 value1 --arg2 value2`
    is equivalent to `TaskArguments(arg1=value1, arg2=value2)`.
    """
    def __init__(self, **args):
        self.args = args

    def get_args(self) -> Dict[str, Any]:
        """
        Gets current arguments in task
        """
        return self.args

    def resolve_for_method(self, method: Callable) -> Dict[str, Any]:
        """
        Evaluates the given arguments against a given signature and ensures
        you can call the method using the indicated arguments.

        Parameters
        ----------
        method: Callabale
            The method that the arguments need to match.

        Returns
        -------
        Dict[str, Any]:
            The arguments that will be indicated to the method with their corresponding typing
            conversion in case requried.
        """
        fullargs = inspect.getfullargspec(method)
        args_annotations = dict(filter(lambda key: key[0] != 'return', fullargs.annotations.items()))
        parsed_args = dict()

        required_args_idxs = len(args_annotations) - len(fullargs.defaults if fullargs.defaults else [])
        for idx, (arg_name, arg_type) in enumerate(args_annotations.items()):
            is_required = idx < required_args_idxs

            if is_required and arg_name not in self.args.keys():
                ValueError(f"Parameter {arg_name} is not optional")

            if arg_type is type(self.args[arg_name]):
                parsed_args[arg_name] = self.args[arg_name]
            elif arg_type is SimpleNamespace and isinstance(self.args[arg_name], str):
                parsed_args[arg_name] = yml2config(self.args[arg_name])
            else:
                raise ValueError(f"Parameter {arg_name} is expecting {arg_type} but got {type(self.args[arg_name])} which is incompatible.")

        return parsed_args
