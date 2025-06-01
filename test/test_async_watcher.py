import asyncio
import os
import sys
import pytest
from pathlib import Path
from typing import List, Tuple

sys.path.append(str(Path(__file__).parent.parent / "src"))

from watcher_fs.async_watcher import AsyncWatcher, AsyncFileWatcher, TriggerType  # Adjust import as needed

pytest_plugins = ('pytest_asyncio',)

@pytest.fixture
def test_dir(tmp_path: Path):
    """Create a temporary directory for tests and clean up after."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    return test_dir

@pytest.fixture
def create_test_files(test_dir: Path):
    """Helper to create test files in the test directory."""
    def _create_files(file_names: List[str]):
        for file_name in file_names:
            file_path = test_dir / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                f.write("Initial content")
    return _create_files

@pytest.mark.asyncio
async def test_per_file_trigger(test_dir: Path, create_test_files):
    """Test PER_FILE trigger type with async callback."""
    create_test_files(["aaa.txt", "bbb.txt"])

    triggered_changes = []

    async def on_change(change: Tuple[str, str]):
        triggered_changes.append(change)

    watcher = AsyncWatcher()
    await watcher.register(
        str(test_dir / "*.txt"),
        on_change,
        trigger_type=TriggerType.PER_FILE,
        callback_extra=True
    )

    await watcher.check()
    assert len(triggered_changes) == 0, "Should detect no changes on initial check"

    triggered_changes.clear()
    with open(test_dir / "aaa.txt", "w") as f:
        f.write("Modified content")
    await asyncio.sleep(0.1)
    await watcher.check()
    assert len(triggered_changes) == 1, "Should detect one modified file"
    expected_change = (str(test_dir / "aaa.txt").replace("\\", "/"), "modified")
    assert expected_change in triggered_changes, f"Expected {expected_change} in triggered_changes"

    triggered_changes.clear()
    os.remove(test_dir / "bbb.txt")
    await asyncio.sleep(0.1)
    await watcher.check()
    assert len(triggered_changes) == 1, "Should detect one deleted file"
    expected_change = (str(test_dir / "bbb.txt").replace("\\", "/"), "deleted")
    assert expected_change in triggered_changes, f"Expected {expected_change} in triggered_changes"

@pytest.mark.asyncio
async def test_any_file_trigger(test_dir: Path, create_test_files):
    """Test ANY_FILE trigger type with async callback."""
    create_test_files(["aaa.txt", "bbb.txt"])

    triggered_changes = []

    async def on_change(changes: List[Tuple[str, str]]):
        triggered_changes.extend(changes)

    watcher = AsyncWatcher()
    await watcher.register(
        str(test_dir / "*.txt"),
        on_change,
        trigger_type=TriggerType.ANY_FILE,
        callback_extra=True
    )

    await watcher.check()
    assert len(triggered_changes) == 0, "Should detect no changes on initial check"

    triggered_changes.clear()
    with open(test_dir / "aaa.txt", "w") as f:
        f.write("Modified content")
    with open(test_dir / "bbb.txt", "w") as f:
        f.write("Modified content")
    await asyncio.sleep(0.1)
    await watcher.check()
    assert len(triggered_changes) == 2, "Should detect two modified files in one callback"
    expected_changes = [
        (str(test_dir / "aaa.txt").replace("\\", "/"), "modified"),
        (str(test_dir / "bbb.txt").replace("\\", "/"), "modified")
    ]
    for expected_change in expected_changes:
        assert expected_change in triggered_changes, f"Expected {expected_change} in triggered_changes"

@pytest.mark.asyncio
async def test_sync_callback(test_dir: Path, create_test_files):
    """Test PER_FILE trigger with synchronous callback."""
    create_test_files(["aaa.txt"])

    triggered_changes = []

    def on_change(change: Tuple[str, str]):
        triggered_changes.append(change)

    watcher = AsyncWatcher()
    await watcher.register(
        str(test_dir / "*.txt"),
        on_change,
        trigger_type=TriggerType.PER_FILE,
        callback_extra=True
    )

    await watcher.check()
    assert len(triggered_changes) == 0, "Should detect no changes on initial check"

    triggered_changes.clear()
    with open(test_dir / "aaa.txt", "w") as f:
        f.write("Modified content")
        f.flush()
        os.fsync(f.fileno())
    await asyncio.sleep(0.2)
    await watcher.check()
    assert len(triggered_changes) == 1, "Should detect one modified file"
    expected_change = (str(test_dir / "aaa.txt").replace("\\", "/"), "modified")
    assert expected_change in triggered_changes, f"Expected {expected_change} in triggered_changes"

@pytest.mark.asyncio
async def test_no_callback_extra(test_dir: Path, create_test_files):
    """Test callback without extra parameters (PER_FILE)."""
    create_test_files(["aaa.txt"])

    call_count = 0

    async def on_change():
        nonlocal call_count
        call_count += 1

    watcher = AsyncWatcher()
    await watcher.register(
        str(test_dir / "*.txt"),
        on_change,
        trigger_type=TriggerType.PER_FILE,
        callback_extra=False
    )

    await watcher.check()
    assert call_count == 0, "Should not call callback on initial check"

    with open(test_dir / "aaa.txt", "w") as f:
        f.write("Modified content")
    await asyncio.sleep(0.1)
    await watcher.check()
    assert call_count == 1, "Should call callback once for modified file"

@pytest.mark.asyncio
async def test_explicit_file_list(test_dir: Path, create_test_files):
    """Test registering explicit file list with ANY_FILE trigger."""
    create_test_files(["aaa.txt", "bbb.txt"])

    triggered_changes = []

    async def on_change(changes: List[Tuple[str, str]]):
        triggered_changes.extend(changes)

    watcher = AsyncWatcher()
    await watcher.register(
        [test_dir / "aaa.txt", test_dir / "bbb.txt"],
        on_change,
        trigger_type=TriggerType.ANY_FILE,
        callback_extra=True
    )

    await watcher.check()
    assert len(triggered_changes) == 0, "Should detect no changes on initial check"

    triggered_changes.clear()
    with open(test_dir / "aaa.txt", "w") as f:
        f.write("Modified content")
        f.flush()
        os.fsync(f.fileno())
    with open(test_dir / "bbb.txt", "w") as f:
        f.write("Modified content")
        f.flush()
        os.fsync(f.fileno())
    await asyncio.sleep(0.2)
    await watcher.check()
    assert len(triggered_changes) == 2, "Should detect two modified files"
    expected_changes = [
        (str(test_dir / "aaa.txt").replace("\\", "/"), "modified"),
        (str(test_dir / "bbb.txt").replace("\\", "/"), "modified")
    ]
    for expected_change in expected_changes:
        assert expected_change in triggered_changes, f"Expected {expected_change} in triggered_changes"

@pytest.mark.asyncio
async def test_last_run_time(test_dir: Path, create_test_files):
    """Test that last_run_time is updated correctly."""
    create_test_files(["aaa.txt"])

    watcher = AsyncWatcher()

    # Register a callback that sleeps for 0.05 seconds
    async def callback():
        await asyncio.sleep(0.05)

    await watcher.register(
        str(test_dir / "*.txt"),
        callback,
        trigger_type=TriggerType.PER_FILE,
        callback_extra=False
    )

    # Initial check (no changes, so callback not triggered)
    await watcher.check()
    assert watcher.last_run_time >= 0, "last_run_time should be non-negative after check"

    # Modify a file to trigger the callback
    with open(test_dir / "aaa.txt", "w") as f:
        f.write("Modified content")
    await asyncio.sleep(0.1)  # Ensure file system updates mtime
    await watcher.check()
    assert watcher.last_run_time >= 0.05, "last_run_time should reflect callback sleep time (0.05s)"

@pytest.mark.asyncio
async def test_empty_directory(test_dir: Path):
    """Test behavior with no files in directory."""
    triggered_changes = []

    async def on_change(change):
        triggered_changes.append(change)

    watcher = AsyncWatcher()
    await watcher.register(
        str(test_dir / "*.txt"),
        on_change,
        trigger_type=TriggerType.PER_FILE,
        callback_extra=True
    )

    await watcher.check()
    assert len(triggered_changes) == 0, "No callbacks should be triggered for empty directory"

@pytest.mark.asyncio
async def test_inaccessible_file(test_dir: Path, create_test_files):
    """Test handling of inaccessible files."""
    create_test_files(["aaa.txt"])
    if os.name != "nt":
        os.chmod(test_dir / "aaa.txt", 0o000)

    triggered_changes = []

    async def on_change(change):
        triggered_changes.append(change)

    watcher = AsyncWatcher()
    await watcher.register(
        str(test_dir / "*.txt"),
        on_change,
        trigger_type=TriggerType.PER_FILE,
        callback_extra=True
    )

    await watcher.check()
    assert len(triggered_changes) == 0, "Inaccessible files should be skipped"

    if os.name != "nt":
        os.chmod(test_dir / "aaa.txt", 0o666)

@pytest.mark.asyncio
async def test_added_files(test_dir: Path, create_test_files):
    """Test detecting newly added files."""
    triggered_changes = []

    async def on_change(change: Tuple[str, str]):
        triggered_changes.append(change)

    watcher = AsyncWatcher()
    await watcher.register(
        str(test_dir / "*.txt"),
        on_change,
        trigger_type=TriggerType.PER_FILE,
        callback_extra=True
    )

    await watcher.check()
    assert len(triggered_changes) == 0, "No changes in empty directory"

    create_test_files(["aaa.txt", "bbb.txt"])
    await asyncio.sleep(0.1)
    await watcher.check()
    assert len(triggered_changes) == 2, "Should detect two added files"
    expected_changes = [
        (str(test_dir / "aaa.txt").replace("\\", "/"), "added"),
        (str(test_dir / "bbb.txt").replace("\\", "/"), "added")
    ]
    for expected_change in expected_changes:
        assert expected_change in triggered_changes, f"Expected {expected_change} in triggered_changes"