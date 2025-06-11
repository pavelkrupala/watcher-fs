import os
import sys
import json
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
from watcher_fs.cli import main, load_config, create_actions_callback, register_watcher_callback
from watcher_fs.watcher import Watcher, TriggerType

sys.path.append(str(Path(__file__).parent.parent / "src"))


# Sample configuration for testing, matching watcher-fs.cfg structure
SAMPLE_CONFIG = {
    "path": "test_dir/**",
    "trigger_type": "any_file",
    "actions": [
        "notify",
        {"action": "cmd", "cmd": "ffprobe {0}"},
        {"action": "cmd", "cmd": "cat {0}"},
        "notify"
    ]
}


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_path = tmp_path / "watcher-fs.cfg"
    with open(config_path, "w") as f:
        json.dump(SAMPLE_CONFIG, f)
        f.flush()
        os.fsync(f.fileno())
    return config_path


@pytest.fixture
def mock_watcher():
    """Provide a mock Watcher instance."""
    with patch("watcher_fs.cli.watcher", spec=Watcher) as mock:
        yield mock


def test_load_config_success(temp_config_file):
    """Test loading a valid configuration file."""
    config = load_config(temp_config_file)
    assert config == SAMPLE_CONFIG


def test_load_config_file_not_found(tmp_path):
    """Test loading a non-existent configuration file."""
    config_path = tmp_path / "nonexistent.cfg"
    with pytest.raises(FileNotFoundError, match=f"Configuration file {config_path.as_posix()} not found"):
        load_config(config_path)


def test_create_actions_callback_single_action():
    """Test creating a callback with a single action."""
    actions_list = ["notify"]
    with patch("watcher_fs.cli.load_action_function") as mock_load:
        mock_action = MagicMock()
        mock_load.return_value = mock_action
        callback = create_actions_callback(actions_list)

        changes = [("file.txt", "modified")]
        callback(changes)

        mock_load.assert_called_once_with("notify")
        mock_action.assert_called_once_with(changes)


def test_create_actions_callback_with_kwargs():
    """Test creating a callback with an action that has kwargs."""
    actions_list = [{"action": "cmd", "cmd": "ffprobe {0}"}]
    with patch("watcher_fs.cli.load_action_function") as mock_load:
        mock_action = MagicMock()
        mock_load.return_value = mock_action
        callback = create_actions_callback(actions_list)

        changes = [("file.txt", "modified")]
        callback(changes)

        mock_load.assert_called_once_with("cmd", {"cmd": "ffprobe {0}"})
        mock_action.assert_called_once_with(changes)


def test_create_actions_callback_error_handling():
    """Test that errors in one action skip subsequent actions."""
    actions_list = ["action1", "action2"]
    with patch("watcher_fs.cli.load_action_function") as mock_load:
        mock_action1 = MagicMock(side_effect=Exception("Action1 failed"))
        mock_action2 = MagicMock()
        mock_load.side_effect = [mock_action1, mock_action2]

        callback = create_actions_callback(actions_list)
        changes = [("file.txt", "modified")]

        with patch("builtins.print") as mock_print:
            callback(changes)

            mock_action1.assert_called_once_with(changes)
            mock_action2.assert_not_called()
            # Check for the actual error message from cli.py
            mock_print.assert_any_call(
                "\033[1;91mError executing action\033[0m \"action1\": Action1 failed"
            )
            mock_print.assert_any_call("\033[1;93m-- Skipping:\033[0m action2")


def test_create_actions_callback_invalid_action_format():
    """Test creating a callback with an invalid action format."""
    actions_list = [{"invalid_key": "value"}]
    with pytest.raises(ValueError,
                       match="Invalid action format: {'invalid_key': 'value'}. Must be a string or a dict with an 'action' key."):
        create_actions_callback(actions_list)


def test_register_watcher_callback_valid_config(temp_config_file, mock_watcher):
    """Test registering a watcher with a valid configuration."""
    config = load_config(temp_config_file)
    with patch("watcher_fs.cli.create_actions_callback") as mock_create_callback:
        mock_callback = MagicMock()
        mock_create_callback.return_value = mock_callback

        with patch("builtins.print") as mock_print:
            register_watcher_callback(config, index=0)

            mock_create_callback.assert_called_once_with(config["actions"])
            mock_watcher.register.assert_called_once_with(
                config["path"],
                mock_callback,
                trigger_type=TriggerType.ANY_FILE,
                callback_extra=True
            )
            mock_print.assert_any_call(
                "Registering: test_dir/** (any_file) - Actions: notify, cmd:{\"cmd\": \"ffprobe {0}\"}, cmd:{\"cmd\": \"cat {0}\"}, notify"
            )


def test_register_watcher_callback_invalid_trigger_type():
    """Test registering a watcher with an invalid trigger type."""
    config = {"path": "test_dir/**", "trigger_type": "invalid", "actions": []}
    with pytest.raises(ValueError,
                       match="Invalid TriggerType value: 'invalid' in cfg #0. Must be one of \\['per_file', 'any_file'\\]"):
        register_watcher_callback(config, index=0)


def test_register_watcher_callback_missing_path():
    """Test registering a watcher with missing path."""
    config = {"trigger_type": "any_file", "actions": []}
    with pytest.raises(RuntimeError, match="Missing existing path in the configuration #0"):
        register_watcher_callback(config, index=0)


def test_main_command_success(temp_config_file, mock_watcher):
    """Test the main CLI command with a valid config."""
    runner = CliRunner()
    with patch("time.sleep", side_effect=KeyboardInterrupt):
        result = runner.invoke(main, ["--config", str(temp_config_file)])

        assert result.exit_code == 0
        assert "Running... Press Ctrl+C to stop" in result.output
        assert "Stopped by user" in result.output
        mock_watcher.check.assert_called()


def test_main_command_config_not_found():
    """Test the main CLI command with a missing config file."""
    runner = CliRunner()
    result = runner.invoke(main, ["--config", "nonexistent.cfg"])
    assert result.exit_code == 1
    # Check for the core error message, accounting for Windows paths
    assert "Configuration file" in result.output
    assert "nonexistent.cfg not found" in result.output


def test_main_command_list_config(temp_config_file, mock_watcher):
    """Test the main CLI command with a list of configs."""
    config_list = [SAMPLE_CONFIG, SAMPLE_CONFIG]
    with open(temp_config_file, "w") as f:
        json.dump(config_list, f)
        f.flush()
        os.fsync(f.fileno())

    with patch("time.sleep", side_effect=KeyboardInterrupt):
        with patch("watcher_fs.cli.register_watcher_callback") as mock_register:
            runner = CliRunner()
            result = runner.invoke(main, ["--config", str(temp_config_file)])

            assert result.exit_code == 0
            assert mock_register.call_count == 2
            mock_register.assert_any_call(config_list[0], index=0)
            mock_register.assert_any_call(config_list[1], index=1)