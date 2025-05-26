import unittest
import os
import sys
import time
import shutil
from pathlib import Path
from typing import Tuple, List, Union

sys.path.append(str(Path(__file__).parent.parent / "src"))

from watcher import Watcher, TriggerType

class TestWatcherList(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = Path("test_dir")
        self.test_dir.mkdir(exist_ok=True)

        # Define test files for .txt and .styl (but don't create them yet)
        self.files = ["aaa.txt", "bbb.txt", "ccc.txt"]
        self.files_style = ["skin.styl", "styl/default.styl", "styl/utils.styl"]

        # Store callback results
        self.callback_results = []

    def tearDown(self):
        # Clean up test directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
        self.callback_results.clear()

    def create_test_files(self, file_names):
        """Helper to create test files."""
        for file_name in file_names:
            file_path = self.test_dir / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                if file_name.endswith(".txt"):
                    f.write("Initial content")
                else:  # .styl
                    f.write("a = #fa0")

    def callback_extra(self, arg: Union[Tuple[str, str], List[Tuple[str, str]]]):
        """Callback for callback_extra=True."""
        # Convert list to tuple for consistency in assertions
        if isinstance(arg, list):
            arg = tuple(arg)
        self.callback_results.append(arg)

    def callback_no_extra(self):
        """Callback for callback_extra=False."""
        self.callback_results.append(None)

    def test_per_file_trigger_txt_extra(self):
        """Test TriggerType.PER_FILE with callback_extra=True for .txt files using list of paths."""
        watcher = Watcher()
        paths = [self.test_dir / f for f in self.files]
        watcher.register(paths, self.callback_extra, TriggerType.PER_FILE, callback_extra=True)

        # Create files after registering
        self.create_test_files(self.files)
        time.sleep(0.1)  # Ensure file system updates

        # Initial check (should detect all .txt files as added)
        watcher.check()
        expected = [
            ((self.test_dir / "aaa.txt").as_posix(), "added"),
            ((self.test_dir / "bbb.txt").as_posix(), "added"),
            ((self.test_dir / "ccc.txt").as_posix(), "added"),
        ]
        self.assertEqual(sorted(self.callback_results), sorted(expected))
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Modify two files
        time.sleep(0.1)  # Ensure modification time changes
        with open(self.test_dir / "aaa.txt", "w") as f:
            f.write("Modified content")
        with open(self.test_dir / "bbb.txt", "w") as f:
            f.write("Modified content")

        # Check for modifications
        watcher.check()
        expected = [
            ((self.test_dir / "aaa.txt").as_posix(), "modified"),
            ((self.test_dir / "bbb.txt").as_posix(), "modified"),
        ]
        self.assertEqual(sorted(self.callback_results), sorted(expected))
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Delete one file
        os.remove(self.test_dir / "ccc.txt")
        watcher.check()
        expected = [((self.test_dir / "ccc.txt").as_posix(), "deleted")]
        self.assertEqual(self.callback_results, expected)
        self.assertGreater(watcher.last_run_time, 0.0)

    def test_per_file_trigger_txt_no_extra(self):
        """Test TriggerType.PER_FILE with callback_extra=False for .txt files using list of paths."""
        watcher = Watcher()
        paths = [self.test_dir / f for f in self.files]
        watcher.register(paths, self.callback_no_extra, TriggerType.PER_FILE, callback_extra=False)

        # Create files after registering
        self.create_test_files(self.files)
        time.sleep(0.1)  # Ensure file system updates

        # Initial check (should trigger callback for each added file)
        watcher.check()
        expected = [None] * 3  # Three files added
        self.assertEqual(self.callback_results, expected)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Modify two files
        time.sleep(0.1)  # Ensure modification time changes
        with open(self.test_dir / "aaa.txt", "w") as f:
            f.write("Modified content")
        with open(self.test_dir / "bbb.txt", "w") as f:
            f.write("Modified content")

        # Check for modifications
        watcher.check()
        expected = [None] * 2  # Two files modified
        self.assertEqual(self.callback_results, expected)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Delete one file
        os.remove(self.test_dir / "ccc.txt")
        watcher.check()
        expected = [None]  # One file deleted
        self.assertEqual(self.callback_results, expected)
        self.assertGreater(watcher.last_run_time, 0.0)

    def test_any_file_trigger_txt_extra(self):
        """Test TriggerType.ANY_FILE with callback_extra=True for .txt files using list of paths."""
        watcher = Watcher()
        paths = [self.test_dir / f for f in self.files]
        watcher.register(paths, self.callback_extra, TriggerType.ANY_FILE, callback_extra=True)

        # Create files after registering
        self.create_test_files(self.files)
        time.sleep(0.1)  # Ensure file system updates

        # Initial check (should trigger once with tuple of all added files)
        watcher.check()
        expected = [tuple([((self.test_dir / f).as_posix(), "added") for f in self.files])]
        self.assertEqual(self.callback_results, expected)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Modify two files
        time.sleep(0.1)  # Ensure modification time changes
        with open(self.test_dir / "aaa.txt", "w") as f:
            f.write("Modified content")
        with open(self.test_dir / "bbb.txt", "w") as f:
            f.write("Modified content")

        # Check for modifications (should trigger once with tuple of modified files)
        watcher.check()
        expected = [tuple([
            ((self.test_dir / "aaa.txt").as_posix(), "modified"),
            ((self.test_dir / "bbb.txt").as_posix(), "modified")
        ])]
        self.assertEqual(self.callback_results, expected)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Delete one file
        os.remove(self.test_dir / "ccc.txt")
        watcher.check()
        expected = [tuple([((self.test_dir / "ccc.txt").as_posix(), "deleted")])]
        self.assertEqual(self.callback_results, expected)
        self.assertGreater(watcher.last_run_time, 0.0)

    def test_any_file_trigger_txt_no_extra(self):
        """Test TriggerType.ANY_FILE with callback_extra=False for .txt files using list of paths."""
        watcher = Watcher()
        paths = [self.test_dir / f for f in self.files]
        watcher.register(paths, self.callback_no_extra, TriggerType.ANY_FILE, callback_extra=False)

        # Create files after registering
        self.create_test_files(self.files)
        time.sleep(0.1)  # Ensure file system updates

        # Initial check (should trigger once)
        watcher.check()
        self.assertEqual(self.callback_results, [None])
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Modify two files
        time.sleep(0.1)  # Ensure modification time changes
        with open(self.test_dir / "aaa.txt", "w") as f:
            f.write("Modified content")
        with open(self.test_dir / "bbb.txt", "w") as f:
            f.write("Modified content")

        # Check for modifications (should trigger once)
        watcher.check()
        self.assertEqual(self.callback_results, [None])
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Delete one file
        os.remove(self.test_dir / "ccc.txt")
        watcher.check()
        self.assertEqual(self.callback_results, [None])
        self.assertGreater(watcher.last_run_time, 0.0)

    def test_invalid_paths(self):
        """Test registering with empty list and non-existent paths."""
        watcher = Watcher()
        paths = [
            self.test_dir / "non_existent.txt",  # Non-existent file
            self.test_dir / "aaa.txt",           # Valid file
            self.test_dir,                       # Directory (invalid)
        ]
        self.create_test_files(["aaa.txt"])  # Create only one valid file
        watcher.register(paths, self.callback_extra, TriggerType.PER_FILE, callback_extra=True)

        # Initial check (should only detect aaa.txt)
        watcher.check()
        expected = []
        self.assertEqual(self.callback_results, expected)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()


    def test_empty_list(self):
        """Test registering with an empty list."""
        watcher = Watcher()
        watcher.register([], self.callback_no_extra, TriggerType.PER_FILE, callback_extra=False)
        watcher.check()
        self.assertEqual(self.callback_results, [])  # No callbacks
        self.assertEqual(watcher.tracked_files, {})  # No tracked files
        self.assertEqual(watcher.file_to_watchers, {})  # No watcher mappings
        self.assertGreater(watcher.last_run_time, 0.0)

if __name__ == "__main__":
    unittest.main()
