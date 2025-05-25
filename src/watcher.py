import glob
import os
from pathlib import Path
from typing import Callable, List, Dict, Set, Tuple
from enum import Enum
import time

class TriggerType(Enum):
    PER_FILE = "per_file"  # Trigger callback for each changed file
    ANY_FILE = "any_file"  # Trigger callback once if any file changes

class FileWatcher:
    def __init__(self, path: str, callback: Callable[..., None], trigger_type: TriggerType, callback_extra: bool = False):
        self.path = path
        self.callback = callback
        self.trigger_type = trigger_type
        self.callback_extra = callback_extra

    def dispatch_callback(self, change: Tuple[str, str] | List[Tuple[str, str]]):
        """Dispatch the callback based on callback_extra setting."""
        if self.callback_extra:
            # For callback_extra=True, pass the change(s) as parameter(s)
            self.callback(change)
        else:
            # For callback_extra=False, call callback without parameters
            self.callback()


class Watcher:
    def __init__(self):
        self.watchers: List[FileWatcher] = []  # List of registered watchers
        self.tracked_files: Dict[str, Tuple[Set[int], float]] = {}  # Maps files to watcher indices
        self.last_run_time: float = 0.0  # Time taken for last check

    def register(self, pattern: str, callback: Callable[..., None], trigger_type: TriggerType = TriggerType.PER_FILE, callback_extra: bool = False):
        """Register a file pattern to watch with a callback and trigger type."""
        watcher = FileWatcher(pattern, callback, trigger_type, callback_extra)
        watcher_index = len(self.watchers)
        self.watchers.append(watcher)

        # Populate initial file list for this pattern
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.isfile(file_path):  # Only track files, not directories
                if file_path not in self.tracked_files:
                    self.tracked_files[file_path] = (set(), os.path.getmtime(file_path))
                self.tracked_files[file_path][0].add(watcher_index)

    def check(self):
        """Check for file changes and trigger callbacks."""
        start_time = time.time()

        # Collect all current files for all patterns
        current_files: Dict[str, Set[int]] = {}
        for watcher_index, watcher in enumerate(self.watchers):
            for file_path in glob.glob(watcher.path, recursive=True):
                if os.path.isfile(file_path):
                    current_files.setdefault(file_path, set()).add(watcher_index)

        # Track which ANY_FILE watchers have been triggered in this cycle
        triggered_any_file: Set[int] = set()
        # Collect changes for ANY_FILE with callback_extra=True
        any_file_changes: Dict[int, List[Tuple[str, str]]] = {i: [] for i in range(len(self.watchers))}


        # Detect deletions
        for file_path in list(self.tracked_files.keys()):
            if file_path not in current_files:
                watcher_indices = self.tracked_files[file_path][0]
                for watcher_index in watcher_indices:
                    watcher = self.watchers[watcher_index]
                    if watcher.trigger_type == TriggerType.PER_FILE:
                        watcher.dispatch_callback((file_path, "deleted"))
                    elif watcher.trigger_type == TriggerType.ANY_FILE and watcher_index not in triggered_any_file:
                        any_file_changes[watcher_index].append((file_path, "deleted"))
                del self.tracked_files[file_path]


        # Detect additions and modifications
        for file_path, watcher_indices in current_files.items():
            current_mtime = os.path.getmtime(file_path)
            if file_path not in self.tracked_files:
                # New file detected
                self.tracked_files[file_path] = (watcher_indices, current_mtime)
                for watcher_index in watcher_indices:
                    watcher = self.watchers[watcher_index]
                    if watcher.trigger_type == TriggerType.PER_FILE:
                        watcher.dispatch_callback((file_path, "added"))
                    elif watcher.trigger_type == TriggerType.ANY_FILE and watcher_index not in triggered_any_file:
                        any_file_changes[watcher_index].append((file_path, "added"))
            else:
                # Check for modifications
                prev_mtime = self.tracked_files[file_path][1]
                if prev_mtime != current_mtime:
                    self.tracked_files[file_path] = (watcher_indices, current_mtime)
                    for watcher_index in watcher_indices:
                        watcher = self.watchers[watcher_index]
                        if watcher.trigger_type == TriggerType.PER_FILE:
                            watcher.dispatch_callback((file_path, "modified"))
                        elif watcher.trigger_type == TriggerType.ANY_FILE and watcher_index not in triggered_any_file:
                            any_file_changes[watcher_index].append((file_path, "modified"))

        # Trigger ANY_FILE callbacks with collected changes
        for watcher_index, changes in any_file_changes.items():
            watcher = self.watchers[watcher_index]
            if watcher.trigger_type == TriggerType.ANY_FILE and changes and watcher_index not in triggered_any_file:
                watcher.dispatch_callback(changes if watcher.callback_extra else [])
                triggered_any_file.add(watcher_index)

        # Record runtime
        self.last_run_time = time.time() - start_time

# Example usage:
if __name__ == "__main__":
    def on_change(file_path: str, change_type: str):
        print(f"File {file_path} {change_type}")

    watcher = Watcher()
    watcher.register("test/test_dir/**/*.txt", on_change, TriggerType.PER_FILE)
    watcher.register("test/test_dir/**/*.styl", on_change, TriggerType.ANY_FILE)

    # Simulate a check
    watcher.check()

    # do something

    # check again
    watcher.check()