# Watcher

A Python package for monitoring file system changes.

## Installation
```bash
pip install fswatcher
```

## Usage

```python
from fswatcher.watcher import Watcher, TriggerType

def on_change():
    print("File changed!")

watcher = Watcher()
watcher.register("path/to/watch", on_change, TriggerType.PER_FILE)
watcher.check()
```

## Documentation

See https://pavelkrupala.github.io/fswatcher