import unittest
import os
import sys
import time
import shutil
from pathlib import Path
from typing import Tuple, List, Union

sys.path.append(str(Path(__file__).parent.parent / "src"))

from watcher_fs.watcher import Watcher, TriggerType

class TestWatcher(unittest.TestCase):
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
        time.sleep(0.05)
        if isinstance(arg, list):
            arg = tuple(arg)
        self.callback_results.append(arg)

    def callback_no_extra(self):
        """Callback for callback_extra=False."""
        time.sleep(0.05)
        self.callback_results.append(None)

    def test_per_file_trigger_txt_extra(self):
        """Test TriggerType.PER_FILE with callback_extra=True for .txt files."""
        watcher = Watcher()
        watcher.register(str(self.test_dir / "**/*.txt"), self.callback_extra, TriggerType.PER_FILE, callback_extra=True)

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
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
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
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Delete one file
        os.remove(self.test_dir / "ccc.txt")
        watcher.check()
        expected = [((self.test_dir / "ccc.txt").as_posix(), "deleted")]
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
        self.assertGreater(watcher.last_run_time, 0.0)

    def test_per_file_trigger_txt_no_extra(self):
        """Test TriggerType.PER_FILE with callback_extra=False for .txt files."""
        watcher = Watcher()
        watcher.register(str(self.test_dir / "**/*.txt"), self.callback_no_extra, TriggerType.PER_FILE, callback_extra=False)

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
        """Test TriggerType.ANY_FILE with callback_extra=True for .txt files."""
        watcher = Watcher()
        watcher.register(str(self.test_dir / "**/*.txt"), self.callback_extra, TriggerType.ANY_FILE, callback_extra=True)

        # Create files after registering
        self.create_test_files(self.files)
        time.sleep(0.1)  # Ensure file system updates

        # Initial check (should trigger once with tuple of all added files)
        watcher.check()
        expected = [tuple([((self.test_dir / f).as_posix(), "added") for f in self.files])]
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
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
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Delete one file
        os.remove(self.test_dir / "ccc.txt")
        watcher.check()
        expected = [tuple([((self.test_dir / "ccc.txt").as_posix(), "deleted")])]
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
        self.assertGreater(watcher.last_run_time, 0.0)

    def test_any_file_trigger_txt_no_extra(self):
        """Test TriggerType.ANY_FILE with callback_extra=False for .txt files."""
        watcher = Watcher()
        watcher.register(str(self.test_dir / "**/*.txt"), self.callback_no_extra, TriggerType.ANY_FILE, callback_extra=False)

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

    def test_per_file_trigger_styl_extra(self):
        """Test TriggerType.PER_FILE with callback_extra=True for .styl files."""
        watcher = Watcher()
        watcher.register(str(self.test_dir / "**/*.styl"), self.callback_extra, TriggerType.PER_FILE, callback_extra=True)

        # Create files after registering
        self.create_test_files(self.files_style)
        time.sleep(0.1)  # Ensure file system updates

        # Initial check (should detect all .styl files as added)
        watcher.check()
        expected = [
            ((self.test_dir / "skin.styl").as_posix(), "added"),
            ((self.test_dir / "styl/default.styl").as_posix(), "added"),
            ((self.test_dir / "styl/utils.styl").as_posix(), "added"),
        ]
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Modify two files
        time.sleep(0.1)  # Ensure modification time changes
        with open(self.test_dir / "skin.styl", "w") as f:
            f.write("a = #0af")
        with open(self.test_dir / "styl/default.styl", "w") as f:
            f.write("a = #0af")

        # Check for modifications
        watcher.check()
        expected = [
            ((self.test_dir / "skin.styl").as_posix(), "modified"),
            ((self.test_dir / "styl/default.styl").as_posix(), "modified"),
        ]
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Delete one file
        os.remove(self.test_dir / "styl/utils.styl")
        watcher.check()
        expected = [((self.test_dir / "styl/utils.styl").as_posix(), "deleted")]
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
        self.assertGreater(watcher.last_run_time, 0.0)

    def test_per_file_trigger_styl_no_extra(self):
        """Test TriggerType.PER_FILE with callback_extra=False for .styl files."""
        watcher = Watcher()
        watcher.register(str(self.test_dir / "**/*.styl"), self.callback_no_extra, TriggerType.PER_FILE, callback_extra=False)

        # Create files after registering
        self.create_test_files(self.files_style)
        time.sleep(0.1)  # Ensure file system updates

        # Initial check (should trigger callback for each added file)
        watcher.check()
        expected = [None] * 3  # Three files added
        self.assertEqual(self.callback_results, expected)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Modify two files
        time.sleep(0.1)  # Ensure modification time changes
        with open(self.test_dir / "skin.styl", "w") as f:
            f.write("a = #0af")
        with open(self.test_dir / "styl/default.styl", "w") as f:
            f.write("a = #0af")

        # Check for modifications
        watcher.check()
        expected = [None] * 2  # Two files modified
        self.assertEqual(self.callback_results, expected)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Delete one file
        os.remove(self.test_dir / "styl/utils.styl")
        watcher.check()
        expected = [None]  # One file deleted
        self.assertEqual(self.callback_results, expected)
        self.assertGreater(watcher.last_run_time, 0.0)

    def test_any_file_trigger_styl_extra(self):
        """Test TriggerType.ANY_FILE with callback_extra=True for .styl files."""
        watcher = Watcher()
        watcher.register(str(self.test_dir / "**/*.styl"), self.callback_extra, TriggerType.ANY_FILE, callback_extra=True)

        # Create files after registering
        self.create_test_files(self.files_style)
        time.sleep(0.1)  # Ensure file system updates

        # Initial check (should trigger once with tuple of all added files)
        watcher.check()
        expected = [tuple([((self.test_dir / f).as_posix(), "added") for f in self.files_style])]
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Modify two files
        time.sleep(0.1)  # Ensure modification time changes
        with open(self.test_dir / "skin.styl", "w") as f:
            f.write("a = #0af")
        with open(self.test_dir / "styl/default.styl", "w") as f:
            f.write("a = #0af")

        # Check for modifications (should trigger once with tuple of modified files)
        watcher.check()
        expected = [tuple([
            ((self.test_dir / "skin.styl").as_posix(), "modified"),
            ((self.test_dir / "styl/default.styl").as_posix(), "modified")
        ])]
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Delete one file
        os.remove(self.test_dir / "styl/utils.styl")
        watcher.check()
        expected = [tuple([((self.test_dir / "styl/utils.styl").as_posix(), "deleted")])]
        for expected_item in expected:
            self.assertIn(expected_item, self.callback_results)
        self.assertGreater(watcher.last_run_time, 0.0)

    def test_any_file_trigger_styl_no_extra(self):
        """Test TriggerType.ANY_FILE with callback_extra=False for .styl files."""
        watcher = Watcher()
        watcher.register(str(self.test_dir / "**/*.styl"), self.callback_no_extra, TriggerType.ANY_FILE, callback_extra=False)

        # Create files after registering
        self.create_test_files(self.files_style)
        time.sleep(0.1)  # Ensure file system updates

        # Initial check (should trigger once)
        watcher.check()
        self.assertEqual(self.callback_results, [None])
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Modify two files
        time.sleep(0.1)  # Ensure modification time changes
        with open(self.test_dir / "skin.styl", "w") as f:
            f.write("a = #0af")
        with open(self.test_dir / "styl/default.styl", "w") as f:
            f.write("a = #0af")

        # Check for modifications (should trigger once)
        watcher.check()
        self.assertEqual(self.callback_results, [None])
        self.assertGreater(watcher.last_run_time, 0.0)
        self.callback_results.clear()

        # Delete one file
        os.remove(self.test_dir / "styl/utils.styl")
        watcher.check()
        self.assertEqual(self.callback_results, [None])
        self.assertGreater(watcher.last_run_time, 0.0)

    def test_unchanged_files_no_update(self):
        """Test that unchanged files don't trigger callbacks or unnecessary updates."""
        watcher = Watcher()
        watcher.register(str(self.test_dir / "**/*.txt"), self.callback_no_extra, TriggerType.PER_FILE, callback_extra=False)

        # Create files after registering
        self.create_test_files(self.files)
        time.sleep(0.1)  # Ensure file system updates

        # Initial check to populate tracked_files
        watcher.check()
        expected = [None] * 3  # Three files added
        self.assertEqual(self.callback_results, expected)
        tracked_files_before = dict(watcher.tracked_files)  # Copy to compare later
        self.callback_results.clear()

        # Run check again with no changes
        watcher.check()
        self.assertEqual(self.callback_results, [])  # No callbacks for unchanged files
        self.assertEqual(watcher.tracked_files, tracked_files_before)  # No updates to tracked_files

if __name__ == "__main__":
    unittest.main()