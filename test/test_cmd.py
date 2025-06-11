import io
import sys
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from watcher_fs.actions.cmd import action, cmd

sys.path.append(str(Path(__file__).parent.parent / "src"))


# ANSI color codes from cmd.py
CON_TEAL = "\033[1;96m"
CON_RESET = "\033[0m"
CON_HEAD = f"{CON_TEAL}[cmd]{CON_RESET}"

@pytest.fixture
def sample_change():
    """Provide a sample single change tuple."""
    return ("file.txt", "modified")

@pytest.fixture
def sample_changes_list():
    """Provide a sample list of changes."""
    return [("file1.txt", "modified"), ("file2.txt", "created")]

@pytest.fixture
def mock_subprocess_popen():
    """Mock subprocess.Popen for testing command execution."""
    mock_process = MagicMock()
    # Simulate text streams with io.StringIO
    mock_process.stdout = io.StringIO("stdout line\n")
    mock_process.stderr = io.StringIO("stderr line\n")
    # Mock poll and wait for process completion
    mock_process.poll.side_effect = [None, 0]  # Process running, then finished
    mock_process.wait.return_value = 0  # Successful exit
    with patch("subprocess.Popen", return_value=mock_process) as mock_popen:
        yield mock_popen

def test_action_with_single_change(sample_change):
    """Test action function with a single change tuple."""
    kwargs = {"cmd": "echo {0}"}
    with patch("watcher_fs.actions.cmd.cmd") as mock_cmd:
        action(sample_change, **kwargs)
        mock_cmd.assert_called_once_with(sample_change[0], event_type=sample_change[1], **kwargs)

def test_action_with_list_of_changes(sample_changes_list):
    """Test action function with a list of changes."""
    kwargs = {"cmd": "echo {0}"}
    with patch("watcher_fs.actions.cmd.cmd") as mock_cmd:
        action(sample_changes_list, **kwargs)
        assert mock_cmd.call_count == 2
        expected_calls = [
            (sample_changes_list[0][0], sample_changes_list[0][1]),  # ('file1.txt', 'modified')
            (sample_changes_list[1][0], sample_changes_list[1][1])   # ('file2.txt', 'created')
        ]
        for file, event_type in expected_calls:
            assert any(
                call == call(file, event_type=event_type, **kwargs)
                for call in mock_cmd.call_args_list
            ), f"Call with args {(file, event_type, kwargs)} not found in {mock_cmd.call_args_list}"

def test_action_with_empty_list():
    """Test action function with an empty list of changes."""
    kwargs = {"cmd": "echo {0}"}
    with patch("watcher_fs.actions.cmd.cmd") as mock_cmd:
        action([], **kwargs)
        mock_cmd.assert_not_called()

def test_cmd_successful_execution(mock_subprocess_popen, capfd):
    """Test cmd function with successful command execution."""
    file = "file.txt"
    event_type = "modified"
    kwargs = {"cmd": "echo {0}"}
    expected_cmd = f"echo {file}"
    expected_stdout_print = [
        f"{CON_HEAD} File {file} ({event_type}), kwargs: {kwargs}",
        f"{CON_HEAD} {expected_cmd}",
        "stdout line\n"
    ]
    expected_stderr_print = [
        "stderr line\n"
    ]

    with patch("builtins.print") as mock_print, \
         patch("sys.stdout.flush") as mock_stdout_flush, \
         patch("sys.stderr.flush") as mock_stderr_flush:

        cmd(file, event_type, **kwargs)

        # Verify print calls
        mock_print.assert_any_call(expected_stdout_print[0])  # First print: default args
        mock_print.assert_any_call(expected_stdout_print[1])  # Second print: default args
        mock_print.assert_any_call(expected_stdout_print[2], end="", flush=True),  # stdout line
        mock_print.assert_any_call(expected_stderr_print[0], file=sys.stderr, end="", flush=True)       # stderr line

        mock_subprocess_popen.assert_called_once_with(
            ['echo', file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        assert mock_stdout_flush.call_count >= 1  # At least twice (for output and final flush)
        assert mock_stderr_flush.call_count >= 1  # At least twice (for output and final flush)

def test_cmd_missing_cmd_kwarg():
    """Test cmd function raises RuntimeError when cmd is missing."""
    file = "file.txt"
    event_type = "modified"
    kwargs = {}
    with pytest.raises(RuntimeError, match="Cmd is not defined properly"):
        cmd(file, event_type, **kwargs)

def test_cmd_command_not_found(mock_subprocess_popen):
    """Test cmd function handles FileNotFoundError."""
    mock_subprocess_popen.side_effect = FileNotFoundError("Command not found")
    file = "file.txt"
    event_type = "modified"
    kwargs = {"cmd": "nonexistent {0}"}
    with pytest.raises(RuntimeError, match=f"Command not found: nonexistent {file}"):
        cmd(file, event_type, **kwargs)

def test_cmd_non_zero_exit_code(mock_subprocess_popen):
    """Test cmd function handles non-zero exit code."""
    mock_subprocess_popen.return_value.poll.side_effect = [None, 1]
    mock_subprocess_popen.return_value.wait.return_value = 1
    file = "file.txt"
    event_type = "modified"
    kwargs = {"cmd": "echo {0}"}
    with pytest.raises(RuntimeError, match="Command failed with exit code 1"):
        cmd(file, event_type, **kwargs)

def test_cmd_generic_exception(mock_subprocess_popen):
    """Test cmd function handles generic exceptions."""
    mock_subprocess_popen.side_effect = Exception("Unexpected error")
    file = "file.txt"
    event_type = "modified"
    kwargs = {"cmd": "echo {0}"}
    with pytest.raises(RuntimeError, match="Command execution failed: Unexpected error"):
        cmd(file, event_type, **kwargs)