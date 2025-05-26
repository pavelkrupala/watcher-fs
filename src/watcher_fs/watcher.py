import glob
import os
from pathlib import Path
from typing import Callable, List, Dict, Set, Tuple, Union
from enum import Enum
import time

class TriggerType(Enum):
    """Enumeration defining the types of file change triggers for Watcher."""
    PER_FILE = "per_file"  # Trigger callback for each changed file
    ANY_FILE = "any_file"  # Trigger callback once if any file changes

class FileWatcher:
    """Manages watching a specific file path or pattern for changes.

        Attributes:
            path: A string (glob pattern) or list of paths to watch.
            callback: Function to call when changes are detected.
            trigger_type: Type of trigger (PER_FILE or ANY_FILE).
            callback_extra: If True, callback receives path and change type.
        """

    def __init__(
        self,
        path: Union[str, List[Union[str, Path]]],
        callback: Callable,
        trigger_type: TriggerType = TriggerType.PER_FILE,
        callback_extra: bool = False
    ):
        """Initialize a FileWatcher instance.

        Args:
            path: Glob pattern (str) or list of file paths to monitor.
            callback: Function to execute on file changes.
            trigger_type: TriggerType enum specifying callback behavior.
            callback_extra: If True, pass (path, change_type) to callback.
        """
        self.path = path
        self.callback = callback
        self.trigger_type = trigger_type
        self.callback_extra = callback_extra

    def dispatch_callback(self, change: Tuple[str, str] | List[Tuple[str, str]]):
        """Execute the callback with the provided argument.

        Args:
            arg: Single (path, change_type) tuple or list of such tuples.
        """
        if self.callback_extra:
            # For callback_extra=True, pass the change(s) as parameter(s)
            self.callback(change)
        else:
            # For callback_extra=False, call callback without parameters
            self.callback()

class Watcher:
    """Monitors file system changes and dispatches callbacks for registered paths.

        Attributes:
            watchers: List of FileWatcher instances tracking paths or patterns.
            tracked_files: Dict mapping file paths to their last modification times.
            file_to_watchers: Dict mapping file paths to indices of associated watchers.
            last_run_time: Timestamp of the last check() call.
        """

    def __init__(self):
        """Initialize a Watcher instance with empty tracking structures."""
        self.watchers: List[FileWatcher] = []  # List of registered watchers
        self.tracked_files: Dict[str, float] = {}  # Maps files to last modification time
        self.file_to_watchers: Dict[str, Set[int]] = {}  # Maps files to fswatcher indices
        self.last_run_time: float = 0.0  # Time taken for last check

    def register(
        self,
        paths: Union[str, List[Union[str, Path]]],
        callback: Callable,
        trigger_type: TriggerType = TriggerType.PER_FILE,
        callback_extra: bool = False
    ):
        """Register a file path or pattern to watch for changes.

        Args:
            paths: Glob pattern (str) or list of file paths to monitor.
            callback: Function to call when changes are detected.
            trigger_type: TriggerType enum (PER_FILE or ANY_FILE).
            callback_extra: If True, pass (path, change_type) to callback.

        Notes:
            - For string paths, uses glob to find matching files.
            - For lists, only tracks existing files at registration.
            - Stores initial modification times for tracked files.
        """
        # Create a new FileWatcher instance
        watcher = FileWatcher(paths, callback, trigger_type, callback_extra)
        watcher_index = len(self.watchers)
        self.watchers.append(watcher)

        if isinstance(paths, str):
            # Pattern-based registration - use glob
            for file_path in glob.glob(paths, recursive=True):
                if os.path.isfile(file_path):
                    # Normalize path to use forward slashes
                    file_path = str(Path(file_path).as_posix())
                    if file_path not in self.tracked_files:
                        try:
                            self.tracked_files[file_path] = os.path.getmtime(file_path)
                            self.file_to_watchers[file_path] = set()
                        except OSError:
                            continue  # Skip inaccessible files
                    self.file_to_watchers[file_path].add(watcher_index)
        else:
            # List-based registration
            for path in paths:
                file_path = Path(path).as_posix()
                if os.path.isfile(file_path):
                    if file_path not in self.tracked_files:
                        try:
                            self.tracked_files[file_path] = os.path.getmtime(file_path)
                            self.file_to_watchers[file_path] = set()
                        except OSError:
                            continue    # Skip inaccessible files
                    self.file_to_watchers[file_path].add(watcher_index)

    def check(self):
        """Check for file changes and dispatch callbacks as needed.

        Updates tracked_files and file_to_watchers based on current file states.
        Detects added, modified, and deleted files, triggering callbacks accordingly.
        Sets last_run_time to the current time.
        """
        start_time = time.time()

        # Collect all current files for all patterns
        current_files: Dict[str, Set[int]] = {}
        for watcher_index, watcher in enumerate(self.watchers):
            if isinstance(watcher.path, str):
                # Pattern-based: use glob
                for file_path in glob.glob(watcher.path, recursive=True):
                    if os.path.isfile(file_path):
                        # Normalize path to use forward slashes
                        file_path = str(Path(file_path).as_posix())
                        current_files.setdefault(file_path, set()).add(watcher_index)
            else:
                # List-base: iterate over paths
                for path in watcher.path:
                    file_path = str(Path(path).as_posix())
                    if os.path.isfile(file_path):
                        current_files.setdefault(file_path, set()).add(watcher_index)

        # Track which ANY_FILE watchers have been triggered
        triggered_any_file: Set[int] = set()
        any_file_changes: Dict[int, List[Tuple[str, str]]] = {i: [] for i in range(len(self.watchers))}

        # Detect deletions
        for file_path in list(self.tracked_files.keys()):
            if file_path not in current_files:
                watcher_indices = self.file_to_watchers.get(file_path, set())
                for watcher_index in watcher_indices:
                    watcher = self.watchers[watcher_index]
                    if watcher.trigger_type == TriggerType.PER_FILE:
                        watcher.dispatch_callback((file_path, "deleted"))
                    elif watcher.trigger_type == TriggerType.ANY_FILE:
                        any_file_changes[watcher_index].append((file_path, "deleted"))
                # Clean up after callbacks
                self.tracked_files.pop(file_path, None)
                self.file_to_watchers.pop(file_path, None)

        # Detect additions and modifications
        for file_path, watcher_indices in current_files.items():
            try:
                current_mtime = os.path.getmtime(file_path)
            except OSError:
                continue  # Skip inaccessible files
            if file_path not in self.tracked_files:
                # New file detected
                self.tracked_files[file_path] = current_mtime
                self.file_to_watchers[file_path] = watcher_indices
                for watcher_index in watcher_indices:
                    watcher = self.watchers[watcher_index]
                    if watcher.trigger_type == TriggerType.PER_FILE:
                        watcher.dispatch_callback((file_path, "added"))
                    elif watcher.trigger_type == TriggerType.ANY_FILE:
                        any_file_changes[watcher_index].append((file_path, "added"))
            else:
                # Check for modifications
                prev_mtime = self.tracked_files[file_path]
                if prev_mtime != current_mtime:
                    self.tracked_files[file_path] = current_mtime
                    self.file_to_watchers[file_path] = watcher_indices
                    for watcher_index in watcher_indices:
                        watcher = self.watchers[watcher_index]
                        if watcher.trigger_type == TriggerType.PER_FILE:
                            watcher.dispatch_callback((file_path, "modified"))
                        elif watcher.trigger_type == TriggerType.ANY_FILE:
                            any_file_changes[watcher_index].append((file_path, "modified"))

        # Trigger ANY_FILE callbacks with collected changes
        for watcher_index, changes in any_file_changes.items():
            if changes and watcher_index not in triggered_any_file:
                watcher = self.watchers[watcher_index]
                watcher.dispatch_callback(changes if watcher.callback_extra else [])
                triggered_any_file.add(watcher_index)

        # Record runtime
        self.last_run_time = time.time() - start_time

# Example usage:
if __name__ == "__main__":
    test_dir = Path("test_dir")
    def on_change_simple():
        print(f"Something changed.")
    def on_change(change):
        print(f"File {change}")

    def create_test_files(file_names):
        """Helper to create test files."""
        for file_name in file_names:
            file_path = test_dir / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                if file_name.endswith(".txt"):
                    f.write("Initial content")
                else:  # .styl
                    f.write("a = #fa0")

    create_test_files(["aaa.txt", "bbb.txt", "ccc.txt"])
    create_test_files(["skin.styl", "styl/default.styl", "styl/utils.styl"])

    watcher = Watcher()
    watcher.register("test_dir/**/*.txt", on_change_simple, TriggerType.PER_FILE)
    # watcher.register("test_dir/**/*.styl", on_change, TriggerType.ANY_FILE, callback_extra=True)
    watcher.register([test_dir / "skin.styl", test_dir / "styl/default.styl", test_dir / "styl/utils.styl"], on_change, TriggerType.ANY_FILE, callback_extra=True)


    # Simulate a check
    watcher.check()

    # do something
    with open(test_dir / "aaa.txt", "w") as f:
        f.write("Modified content")
    with open(test_dir / "bbb.txt", "w") as f:
        f.write("Modified content")

    with open(test_dir / "skin.styl", "w") as f:
        f.write("a = #0af")
    with open(test_dir / "styl/default.styl", "w") as f:
        f.write("a = #f00")

    # check again
    watcher.check()