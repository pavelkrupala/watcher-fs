# Watcher

A Python package for monitoring file system changes.

## Installation
```bash
pip install watcher-fs
```

## Usage

```python
   from watcher_fs.watcher import Watcher, TriggerType
   from pathlib import Path 
   
   test_dir = Path("test_dir")

   def on_change_simple():
      print(f"Something changed.")

   def on_change(change):
      print(f"File {change}")

   watcher = Watcher()
   
   # register as glob pattern
   watcher.register("test_dir/**/*.txt", on_change_simple, TriggerType.PER_FILE)
   watcher.register("test_dir/**/*.py", on_change, TriggerType.ANY_FILE, callback_extra=True)
   
   # register as list of specified files
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

```

## Documentation

See https://pavelkrupala.github.io/watcher-fs