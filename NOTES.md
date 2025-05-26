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


