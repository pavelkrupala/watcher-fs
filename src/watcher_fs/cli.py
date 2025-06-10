import json
import time
from functools import partial
from typing import List, Union, Dict

import click
import importlib
from pathlib import Path
from watcher_fs.watcher import Watcher, TriggerType

watcher = Watcher()

# ANSI color codes
CON_YELLOW = "\033[1;93m"
CON_RED = "\033[1;91m"
CON_RESET = "\033[0m"    # Reset to default


def load_config(config_path="watcher-fs.cfg"):
    """Load configuration from a JSON file."""
    config_path = Path(config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file {config_path.as_posix()} not found")

    with config_path.open("r") as f:
        return json.load(f)

def load_action_function(action_name: str, kwargs: Dict = None) -> callable:
    """Load the 'action' function from a module, optionally binding kwargs with partial."""
    try:
        module_path = f"watcher_fs.actions.{action_name}"
        module = importlib.import_module(module_path)
        if not hasattr(module, "action"):
            raise AttributeError(f"Module {module_path} does not have an 'action' function.")
        return partial(module.action, **kwargs) if kwargs else module.action
    except ImportError as e:
        raise ImportError(f"Failed to import module {module_path}: {e}")


def create_actions_callback(actions_list: List[Union[str, Dict]]) -> callable:
    """
    Create a callback function that dynamically loads and executes action functions from actions_list.

    Args:
        actions_list: List of actions, each a string or dict with 'action' key and other params.

    Returns:
        A callback function that takes a 'changes' parameter and executes all action functions.
    """
    action_functions = []

    for action in actions_list:
        if isinstance(action, str):
            action_functions.append((action, action, load_action_function(action)))
        elif isinstance(action, dict) and "action" in action:
            kwargs = {k: v for k, v in action.items() if k != "action"}
            action_functions.append((action["action"], action, load_action_function(action["action"], kwargs)))
        else:
            raise ValueError(f"Invalid action format: {action}. Must be a string or a dict with an 'action' key.")

    def actions_callback(changes):
        """Execute all action functions for the given changes, logging errors after execution."""
        error_occured = False
        for action_name, action, action_func in action_functions:
            if error_occured:
                print(f"{CON_YELLOW}-- Skipping:{CON_RESET} {json.dumps(action) if type(action)==dict else action_name}")
            else:
                try:
                    action_func(changes)
                except Exception as e:
                    error_occured = True
                    # Log all errors after execution
                    # print(f"Error executing action {action_name} with {json.dumps(action)}: {error}")
                    print(f"{CON_RED}Error executing action{CON_RESET} {json.dumps(action)}: {e}")

    return actions_callback

def register_watcher_callback(config, index=0):
    path = config.get('path', None)

    if path is None:
        raise RuntimeError(f"Missing existing path in the configuration #{index}")

    trigger_type_str = config.get('trigger_type', 'per_file')
    try:
        trigger_type = TriggerType(trigger_type_str)
    except ValueError:
        raise ValueError(f"Invalid TriggerType value: '{trigger_type_str}' in cfg #{index}. Must be one of {[e.value for e in TriggerType]}")

    actions_list = config.get('actions', [])
    actions_callback = create_actions_callback(actions_list)
    actions_list_str = []
    for a in actions_list:
        if type(a) == str: actions_list_str.append(a)
        elif type(a) == dict: actions_list_str.append(f"{a['action']}:{json.dumps({k: v for k, v in a.items() if k != 'action'})}")

    print(f"Registering: {path} ({trigger_type_str}) - Actions: {", ".join(actions_list_str)}")

    watcher.register(path, actions_callback, trigger_type=trigger_type, callback_extra=True)

@click.command()
@click.option("--config", default="watcher-fs.cfg", help="Path to the configuration file")
def main(config:str):
    """watcher-fs: A command-line tool to perform filesystem actions based on configuration."""
    try:
        config_data = load_config(config)

        if type(config_data) != list:
            config_data = [config_data]

        for ix in range(len(config_data)):
            register_watcher_callback(config_data[ix], index=ix)

        print("Running... Press Ctrl+C to stop")

        while True:
            watcher.check()
            time.sleep(1)


    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise click.Abort()


if __name__ == '__main__':
    main()