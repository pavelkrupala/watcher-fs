## Usefull commands

### Setup
```bash
pip install -r requirements-dev.txt
```

### Run tests
```bash
pytest test 
```

### Build
```bash
python -m build --wheel
```

To build sdist + wheel

```bash
python -m build 
```


### Upload to PyPI
```bash
twine upload dist/* --config-file .pypirc
```

### .pypirc
```ini
[pypi]
username = __token__
password = pypi-XXXX
```

### Build Docs
```bash
cd docs
make clean
make html
```


### Create cmd line command

modify pyproject.toml:
```toml
[project.scripts]
watcher-fs = "watcher_fs.cli:main"
```

add new script `cli.py`:
```python
def main():
    print("Hello World!")
```

### Install package in interactive development mode:

This will install the regular pip package, however it's redirected to the actual code in the repo/dir. 
So any changes you make are immediatelly live.

```bash
pip install -e .
```

Now your cli command works, try:
```bash
watcher-fs
```