.. Watcher documentation master file, created by
   sphinx-quickstart on Mon May 26 21:19:32 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Watcher-FS documentation
========================


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules

Example
=======

.. code-block:: python

   from watcher_fs.watcher import Watcher, TriggerType


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
   watcher.register([
      test_dir / "skin.styl",
      test_dir / "styl/default.styl",
      test_dir / "styl/utils.styl"
   ], on_change, TriggerType.ANY_FILE, callback_extra=True)

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


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`