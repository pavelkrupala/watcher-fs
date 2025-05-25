import glob
import os
from pathlib import Path
from typing import Callable, List, Dict, Set
from enum import Enum
import time

class TriggerType(Enum):
    PER_FILE = "per_file"  # Trigger callback for each changed file
    ANY_FILE = "any_file"  # Trigger callback once if any file changes

class FileWatcher:
    def __init__(self, path: str, callback: Callable[[str, str], None], trigger_type: TriggerType):
        self.path = path
        self.callback = callback
        self.trigger_type = trigger_type
        self.last_modified: Dict[str, float] = {}  # Tracks last modified time per file

class Watcher:
    def __init__(self):
        self.watchers: List[FileWatcher] = []  # List of registered watchers
        self.tracked_files: Dict[str, Set[int]] = {}  # Maps files to watcher indices
        self.last_run_time: float = 0.0  # Time taken for last check

    def register(self, pattern: str, callback: Callable[[str, str], None], trigger_type: TriggerType = TriggerType.PER_FILE):
        """Register a file pattern to watch with a callback and trigger type."""
        watcher = FileWatcher(pattern, callback, trigger_type)
        watcher_index = len(self.watchers)
        self.watchers.append(watcher)

        # Populate initial file list for this pattern
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.isfile(file_path):  # Only track files, not directories
                self.tracked_files.setdefault(file_path, set()).add(watcher_index)
                watcher.last_modified[file_path] = os.path.getmtime(file_path)

    def check(self):
        """Check for file changes and trigger callbacks."""
        start_time = time.time()

        # Collect all current files for all patterns
        current_files: Dict[str, Set[int]] = {}
        for watcher_index, watcher in enumerate(self.watchers):
            for file_path in glob.glob(watcher.path, recursive=True):
                if os.path.isfile(file_path):
                    current_files.setdefault(file_path, set()).add(watcher_index)

        # Detect deletions
        for file_path in list(self.tracked_files.keys()):
            if file_path not in current_files:
                for watcher_index in self.tracked_files[file_path]:
                    watcher = self.watchers[watcher_index]
                    if watcher.trigger_type == TriggerType.PER_FILE:
                        watcher.callback(file_path, "deleted")
                    elif watcher.trigger_type == TriggerType.ANY_FILE:
                        watcher.callback(file_path, "deleted")
                        break  # Trigger once for ANY_FILE
                del self.tracked_files[file_path]

        # Detect additions and modifications
        for file_path, watcher_indices in current_files.items():
            for watcher_index in watcher_indices:
                watcher = self.watchers[watcher_index]
                current_mtime = os.path.getmtime(file_path)

                if file_path not in watcher.last_modified:
                    # New file detected
                    watcher.last_modified[file_path] = current_mtime
                    if watcher.trigger_type == TriggerType.PER_FILE:
                        watcher.callback(file_path, "added")
                    elif watcher.trigger_type == TriggerType.ANY_FILE:
                        watcher.callback(file_path, "added")
                        break  # Trigger once for ANY_FILE
                elif watcher.last_modified[file_path] != current_mtime:
                    # File modified
                    watcher.last_modified[file_path] = current_mtime
                    if watcher.trigger_type == TriggerType.PER_FILE:
                        watcher.callback(file_path, "modified")
                    elif watcher.trigger_type == TriggerType.ANY_FILE:
                        watcher.callback(file_path, "modified")
                        break  # Trigger once for ANY_FILE

        # Update tracked files
        self.tracked_files = current_files

        # Record runtime
        self.last_run_time = time.time() - start_time

# Example usage:
if __name__ == "__main__":
    def on_change(file_path: str, change_type: str):
        print(f"File {file_path} {change_type}")

    watcher = Watcher()
    watcher.register("test_dir/**/*.txt", on_change, TriggerType.PER_FILE)
    watcher.register("test_dir/**/*.py", on_change, TriggerType.ANY_FILE)

    # Simulate a check
    watcher.check()