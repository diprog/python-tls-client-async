@echo off
python -m pip install --upgrade build twine
python -m build --sdist --wheel --outdir dist/
twine upload dist/*