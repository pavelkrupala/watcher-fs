import sys
import pytest
from unittest.mock import patch
from pathlib import Path
from watcher_fs.actions.notify import action, notify

sys.path.append(str(Path(__file__).parent.parent / "src"))


# ANSI color codes from notify.py
CON_GREEN = "\033[1;32m"
CON_RESET = "\033[0m"
CON_HEAD = f"{CON_GREEN}[notify]{CON_RESET}"


@pytest.fixture
def sample_change():
    """Provide a sample single change tuple."""
    return ("file.txt", "modified")


@pytest.fixture
def sample_changes_list():
    """Provide a sample list of changes."""
    return [("file1.txt", "modified"), ("file2.txt", "created")]


def test_action_with_single_change(sample_change):
    """Test action function with a single change tuple."""
    with patch("watcher_fs.actions.notify.notify") as mock_notify:
        action(sample_change)
        mock_notify.assert_called_once_with(sample_change[0], event_type=sample_change[1])


def test_action_with_list_of_changes(sample_changes_list):
    """Test action function with a list of changes."""
    with patch("watcher_fs.actions.notify.notify") as mock_notify:
        action(sample_changes_list)
        assert mock_notify.call_count == 2
        # Check calls flexibly, allowing positional or keyword arguments
        expected_calls = [
            (sample_changes_list[0][0], sample_changes_list[0][1]),  # ('file1.txt', 'modified')
            (sample_changes_list[1][0], sample_changes_list[1][1])  # ('file2.txt', 'created')
        ]
        for file, event_type in expected_calls:
            assert any(
                call == call(file, event_type) or call == call(file, event_type=event_type)
                for call in mock_notify.call_args_list
            ), f"Call with args {(file, event_type)} not found in {mock_notify.call_args_list}"


def test_action_with_empty_list():
    """Test action function with an empty list of changes."""
    with patch("watcher_fs.actions.notify.notify") as mock_notify:
        action([])
        mock_notify.assert_not_called()


def test_notify_output():
    """Test notify function prints the correct message with ANSI colors."""
    file_path = Path("file.txt")
    event_type = "modified"
    expected_output = f"{CON_HEAD} File {file_path} has been {event_type}"

    with patch("builtins.print") as mock_print:
        notify(file_path, event_type)
        mock_print.assert_called_once_with(expected_output)


def test_notify_with_different_event_type():
    """Test notify function with a different event type."""
    file_path = Path("document.pdf")
    event_type = "created"
    expected_output = f"{CON_HEAD} File {file_path} has been {event_type}"

    with patch("builtins.print") as mock_print:
        notify(file_path, event_type)
        mock_print.assert_called_once_with(expected_output)


def test_notify_with_nested_path():
    """Test notify function handles nested Path objects correctly."""
    file_path = Path("folder/subfolder/file.txt")
    event_type = "deleted"
    expected_output = f"{CON_HEAD} File {file_path} has been {event_type}"

    with patch("builtins.print") as mock_print:
        notify(file_path, event_type)
        mock_print.assert_called_once_with(expected_output)


def test_notify_with_empty_path():
    """Test notify function with an empty file path."""
    file_path = Path("")
    event_type = "modified"
    expected_output = f"{CON_HEAD} File {file_path} has been {event_type}"

    with patch("builtins.print") as mock_print:
        notify(file_path, event_type)
        mock_print.assert_called_once_with(expected_output)